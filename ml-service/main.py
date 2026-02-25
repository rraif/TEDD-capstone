from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import BertForSequenceClassification, BertTokenizer
import torch
import torch.nn.functional as F
import os
import logging
import joblib
import re
import email
from email import policy
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from typing import Optional, List, Dict
from features import HTMLFeatures, URLFeatures, TextFeatures, HeaderFeatures

logging.basicConfig(level=logging.INFO)

BERT_MODEL_PATH = "./tedd_bert_final"
URL_MODEL_PATH = "./URLClassifier.joblib"
HTML_MODEL_PATH = "./HTMLClassifier.joblib"

try:
    print(f"Loading BERT model from {BERT_MODEL_PATH}...")
    tokenizer = BertTokenizer.from_pretrained(BERT_MODEL_PATH)
    bert_model = BertForSequenceClassification.from_pretrained(BERT_MODEL_PATH)
    bert_model.eval()
    print("✅ BERT Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading BERT model: {e}")
    bert_model = None

# Load URL Model (Joblib)
url_model = None
try:
    if os.path.exists(URL_MODEL_PATH):
        print(f"Loading URL model from {URL_MODEL_PATH}...")
        url_model = joblib.load(URL_MODEL_PATH)
        print("✅ URL Model loaded successfully!")
    else:
        print(f"⚠️ URL model not found at {URL_MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading URL model: {e}")
    url_model = None

# Load HTML Model (Joblib)
html_model = None
try:
    if os.path.exists(HTML_MODEL_PATH):
        print(f"Loading HTML model from {HTML_MODEL_PATH}...")
        html_model = joblib.load(HTML_MODEL_PATH)
        print("✅ HTML Model loaded successfully!")
    else:
        print(f"⚠️ HTML model not found at {HTML_MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading HTML model: {e}")
    html_model = None

app = FastAPI()

class TextInput(BaseModel):
    text: str

class EmailInput(BaseModel):
    header: Optional[str] = ""
    html: Optional[str] = ""
    urls: Optional[List[str]] = []
    text: Optional[str] = ""

class RawEmailInput(BaseModel):
    email_content: str 

@app.get("/")
def read_root():
    return {"message": "Welcome to the TEDD Phishing Detection API!"}

# ============================================================
# EMAIL PARSING FUNCTIONS
# ============================================================

def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return list(set(re.findall(url_pattern, text)))

def parse_raw_email(raw_email: str) -> Dict:
    """
    Parse raw email content (RFC 2822 format) and extract features using get_features().
    Returns: header info, parsed text/HTML, extracted URL features, and HTML features
    """
    try:
        # Parse email using email.policy.default
        msg = email.message_from_string(raw_email, policy=policy.default)
        
        # Extract header information
        header_dict = {
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "subject": msg.get("Subject", ""),
            "date": msg.get("Date", ""),
            "cc": msg.get("Cc", ""),
            "bcc": msg.get("Bcc", ""),
            "reply_to": msg.get("Reply-To", ""),
            # Authentication headers
            "delivered_to": msg.get("Delivered-To", ""),
            "return_path": msg.get("Return-Path", ""),
            "message_id": msg.get("Message-ID", ""),
            "x_originating_ip": msg.get("X-Originating-IP", ""),
            "x_mailer": msg.get("X-Mailer", ""),
            # Authentication results
            "dkim_result": msg.get("DKIM-Signature", ""),
            "authentication_results": msg.get("Authentication-Results", ""),
            "received_spf": msg.get("Received-SPF", ""),
            # Multiple received headers (potential spoofing indicator)
            "received_headers": msg.get_all("Received", []),
            # Arc headers
            "arc_seal": msg.get("ARC-Seal", ""),
            "arc_message_signature": msg.get("ARC-Message-Signature", ""),
            "arc_authentication_results": msg.get("ARC-Authentication-Results", ""),
            # Other security headers
            "x_forwarded_for": msg.get("X-Forwarded-For", ""),
            "x_forwarded_encrypted": msg.get("X-Forwarded-Encrypted", "")
        }
        header_str = f"From: {header_dict['from']} To: {header_dict['to']} Subject: {header_dict['subject']}"
        
        # Extract body and HTML
        body_text = ""
        html_content = ""
        
        if msg.is_multipart():
            for part in msg.iter_parts():
                content_type = part.get_content_type()
                payload = part.get_payload(decode=True)
                
                if payload:
                    try:
                        decoded = payload.decode('utf-8', errors='ignore')
                    except:
                        decoded = str(payload)
                    
                    if content_type == "text/plain":
                        body_text += decoded
                    elif content_type == "text/html":
                        html_content += decoded
        else:
            # Single part email
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    decoded = payload.decode('utf-8', errors='ignore')
                except:
                    decoded = str(payload)
                
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    body_text = decoded
                elif content_type == "text/html":
                    html_content = decoded
                else:
                    body_text = decoded
        
        # Extract URLs from both text and HTML
        urls = []
        if body_text:
            urls.extend(extract_urls_from_text(body_text))
        if html_content:
            urls.extend(extract_urls_from_text(html_content))
        urls = list(set(urls))  # Remove duplicates
        
        # Extract features using get_features()
        logging.info(f"📧 Extracting features from email...")
        
        # Text features
        text_features = {}
        combined_text = (header_str + " " + body_text).strip()
        if combined_text:
            text_extractor = TextFeatures(combined_text)
            text_features = text_extractor.get_features()
            logging.info(f"  ✅ Text features: {len(text_features)} extracted")
        
        # URL features
        url_features_list = []
        if urls:
            for url in urls:
                try:
                    url_extractor = URLFeatures(url)
                    url_feat = url_extractor.get_features()
                    url_features_list.append({
                        "url": url,
                        "features": url_feat
                    })
                except Exception as e:
                    logging.error(f"Error extracting URL features for {url}: {e}")
            logging.info(f"  ✅ URL features: {len(url_features_list)} URLs analyzed")
        
        # HTML features
        html_features = {}
        if html_content:
            try:
                html_extractor = HTMLFeatures(html_content)
                html_features = html_extractor.get_features()
                logging.info(f"  ✅ HTML features: {len(html_features)} extracted")
            except Exception as e:
                logging.error(f"Error extracting HTML features: {e}")
        
        # Header features
        header_features = {}
        try:
            header_extractor = HeaderFeatures(header_dict)
            header_features = header_extractor.get_features()
            logging.info(f"  ✅ Header features: {len(header_features)} extracted")
        except Exception as e:
            logging.error(f"Error extracting header features: {e}")
        
        return {
            "header": header_str,
            "text": body_text,
            "html": html_content,
            "urls": urls,
            "header_details": header_dict,
            "extracted_features": {
                "header_features": header_features,
                "text_features": text_features,
                "url_features": url_features_list,
                "html_features": html_features
            },
            "parsing_status": "success"
        }
    
    except Exception as e:
        logging.error(f"Email parsing error: {e}")
        return {
            "header": "",
            "text": "",
            "html": "",
            "urls": [],
            "header_details": {},
            "extracted_features": {
                "header_features": {},
                "text_features": {},
                "url_features": [],
                "html_features": {}
            },
            "parsing_status": "error",
            "error": str(e)
        }

# ============================================================
# PREDICTION FUNCTIONS
# ============================================================

def predict_text_bert(text: str) -> Dict:
    """BERT model prediction on email body/text"""
    if bert_model is None or tokenizer is None:
        return {"model": "BERT", "error": "BERT model not loaded"}
    
    try:
        if not text or len(text.strip()) == 0:
            return {"model": "BERT", "prediction": "No text", "confidence": 0.0}
        
        inputs = tokenizer(
            text,
            return_tensors="pt", 
            truncation=True, 
            padding=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = bert_model(**inputs)
        
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)
        
        labels = ["Legitimate", "Phishing"]
        result = labels[predicted_class.item()]
        
        logging.info(f"✅ BERT Prediction: {result} (confidence: {confidence.item():.4f})")
        
        return {
            "model": "BERT",
            "prediction": result,
            "confidence": round(float(confidence.item()), 4),
            "class": int(predicted_class.item())
        }
    except Exception as e:
        logging.error(f"BERT prediction error: {e}")
        return {"model": "BERT", "error": str(e)}

def predict_url_features(urls: List[str]) -> Dict:
    """URL model prediction using extracted features"""
    if url_model is None:
        return {"model": "URL", "error": "URL model not loaded"}
    
    try:
        if not urls or len(urls) == 0:
            return {"model": "URL", "prediction": "No URLs", "confidence": 0.0, "urls_count": 0}
        
        logging.info(f"Processing {len(urls)} URLs...")
        all_predictions = []
        all_confidences = []
        
        for url in urls:
            try:
                # Extract URL features
                url_extractor = URLFeatures(url)
                features_dict = url_extractor.get_features()
                features_list = [list(features_dict.values())]
                
                # Predict
                prediction = url_model.predict(features_list)[0]
                probabilities = url_model.predict_proba(features_list)[0]
                confidence = max(probabilities)
                
                all_predictions.append(prediction)
                all_confidences.append(confidence)
                
                logging.info(f"  URL: {url[:50]}... → {['Legitimate', 'Phishing'][int(prediction)]} ({confidence:.4f})")
            except Exception as e:
                logging.error(f"Error processing URL {url}: {e}")
                continue
        
        if not all_predictions:
            return {"model": "URL", "error": "Failed to process all URLs"}
        
        # Aggregate predictions (majority vote weighted by confidence)
        phishing_score = sum(1 for p in all_predictions if p == 1) / len(all_predictions)
        avg_confidence = sum(all_confidences) / len(all_confidences)
        final_prediction = "Phishing" if phishing_score >= 0.5 else "Legitimate"
        
        return {
            "model": "URL",
            "prediction": final_prediction,
            "confidence": round(avg_confidence, 4),
            "urls_analyzed": len(urls),
            "phishing_ratio": round(phishing_score, 4)
        }
    except Exception as e:
        logging.error(f"URL prediction error: {e}")
        return {"model": "URL", "error": str(e)}

def predict_html_features(html_text: str) -> Dict:
    """HTML model prediction using extracted features"""
    if html_model is None:
        return {"model": "HTML", "error": "HTML model not loaded"}
    
    try:
        if not html_text or len(html_text.strip()) == 0:
            return {"model": "HTML", "prediction": "No HTML", "confidence": 0.0}
        
        logging.info("Extracting HTML features...")
        
        # Extract HTML features
        html_extractor = HTMLFeatures(html_text)
        features_dict = html_extractor.get_features()
        features_list = [list(features_dict.values())]
        
        # Predict
        prediction = html_model.predict(features_list)[0]
        probabilities = html_model.predict_proba(features_list)[0]
        confidence = max(probabilities)
        
        labels = ["Legitimate", "Phishing"]
        result = labels[int(prediction)]
        
        logging.info(f"✅ HTML Prediction: {result} (confidence: {confidence:.4f})")
        
        return {
            "model": "HTML",
            "prediction": result,
            "confidence": round(float(confidence), 4),
            "class": int(prediction)
        }
    except Exception as e:
        logging.error(f"HTML prediction error: {e}")
        return {"model": "HTML", "error": str(e)}

def calculate_total_phishing_score(predictions: List[Dict]) -> Dict:
    """
    Calculate combined phishing score from all models.
    Returns total score and final prediction.
    """
    valid_predictions = [p for p in predictions if "error" not in p]
    
    if not valid_predictions:
        return {
            "total_score": 0.0,
            "final_prediction": "Unable to predict",
            "models_used": 0
        }
    
    # Weighted average (BERT=30%, URL=40%, HTML=30%)
    weights = {
        "BERT": 0.3,
        "URL": 0.4,
        "HTML": 0.3
    }
    
    weighted_sum = 0
    total_weight = 0
    prediction_details = []
    
    for pred in valid_predictions:
        model_name = pred.get("model", "")
        prediction = pred.get("prediction", "Legitimate")
        confidence = pred.get("confidence", 0.5)
        
        # Convert prediction to score (0=Legitimate, 1=Phishing)
        pred_score = 1.0 if prediction == "Phishing" else 0.0
        weight = weights.get(model_name, 0.1)
        
        weighted_score = (pred_score * confidence) * weight
        weighted_sum += weighted_score
        total_weight += weight
        
        prediction_details.append({
            "model": model_name,
            "prediction": prediction,
            "confidence": confidence,
            "weight": weight,
            "weighted_score": round(weighted_score, 4)
        })
    
    total_score = weighted_sum / total_weight if total_weight > 0 else 0
    final_prediction = "Phishing" if total_score >= 0.5 else "Legitimate"
    
    logging.info(f"📊 TOTAL SCORE: {total_score:.4f} → {final_prediction}")
    
    return {
        "total_score": round(total_score, 4),
        "final_prediction": final_prediction,
        "threshold": 0.5,
        "models_used": len(valid_predictions),
        "prediction_breakdown": prediction_details
    }

@app.post("/parse-and-predict")
async def parse_and_predict_endpoint(raw_email: RawEmailInput):
    """
    Parse raw email content and automatically run comprehensive phishing detection.
    Separates email into: header, body, text, HTML, and extracts URLs.
    Then runs predictions through all models.
    """
    logging.info("=" * 60)
    logging.info("📨 PARSING RAW EMAIL AND RUNNING DETECTION")
    logging.info("=" * 60)
    
    try:
        # 1️⃣ Parse the raw email
        logging.info("\n1️⃣ Parsing email content...")
        parsed_email = parse_raw_email(raw_email.email_content)
        
        if parsed_email["parsing_status"] == "error":
            raise HTTPException(status_code=400, detail=f"Email parsing failed: {parsed_email.get('error', 'Unknown error')}")
        
        logging.info(f"✅ Email parsed successfully")
        
        # 2️⃣ Create EmailInput from parsed data
        email_input = EmailInput(
            header=parsed_email["header"],
            html=parsed_email["html"],
            urls=parsed_email["urls"],
            text=parsed_email["text"]
        )
        
        # 3️⃣ Run comprehensive prediction
        logging.info("\n2️⃣ Running comprehensive phishing detection...")
        predictions = []
        
        # BERT prediction on combined text
        combined_text = ""
        if parsed_email["header"]:
            combined_text += parsed_email["header"] + " "
        if parsed_email["text"]:
            combined_text += parsed_email["text"]
        
        if combined_text.strip():
            bert_result = predict_text_bert(combined_text)
            predictions.append(bert_result)
        
        # URL prediction
        if parsed_email["urls"] and len(parsed_email["urls"]) > 0:
            url_result = predict_url_features(parsed_email["urls"])
            predictions.append(url_result)
        
        # HTML prediction
        if parsed_email["html"] and len(parsed_email["html"].strip()) > 0:
            html_result = predict_html_features(parsed_email["html"])
            predictions.append(html_result)
        
        # Calculate total score
        total_result = calculate_total_phishing_score(predictions)
        
        logging.info("=" * 60)
        logging.info("✅ DETECTION COMPLETE")
        logging.info("=" * 60 + "\n")
        
        return {
            "parsed_email": {
                "header": parsed_email["header"],
                "text_length": len(parsed_email["text"]),
                "html_length": len(parsed_email["html"]),
                "urls_found": len(parsed_email["urls"]),
                "header_details": parsed_email["header_details"],
                "urls": parsed_email["urls"]
            },
            "extracted_features": parsed_email["extracted_features"],
            "individual_predictions": predictions,
            "combined_analysis": total_result
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Parse and predict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

