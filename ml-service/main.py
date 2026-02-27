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
import tldextract 
from bs4 import BeautifulSoup
from email import policy
from urllib.parse import urlparse
from typing import List, Dict
from features import HTMLFeatures, URLFeatures
from collections import Counter

logging.basicConfig(level=logging.INFO)

BERT_MODEL_PATH = "./tedd_bert_final"
URL_MODEL_PATH = "./URLClassifier.joblib"
HTML_MODEL_PATH = "./HTMLClassifier.joblib"

# Load BERT Model
try:
    tokenizer = BertTokenizer.from_pretrained(BERT_MODEL_PATH)
    bert_model = BertForSequenceClassification.from_pretrained(BERT_MODEL_PATH)
    bert_model.eval()
    logging.info("✅ BERT Model loaded successfully!")
except Exception as e:
    logging.error(f"❌ Error loading BERT model: {e}")
    bert_model = None

# Load URL Model
try:
    url_model = joblib.load(URL_MODEL_PATH) if os.path.exists(URL_MODEL_PATH) else None
    if url_model: logging.info("✅ URL Model loaded successfully!")
except Exception as e:
    logging.error(f"❌ Error loading URL model: {e}")

# Load HTML Model
try:
    html_model = joblib.load(HTML_MODEL_PATH) if os.path.exists(HTML_MODEL_PATH) else None
    if html_model: logging.info("✅ HTML Model loaded successfully!")
except Exception as e:
    logging.error(f"❌ Error loading HTML model: {e}")

app = FastAPI()

class RawEmailInput(BaseModel):
    email_content: str 

@app.get("/")
def read_root():
    return {"message": "Welcome to the TEDD Phishing Detection API!"}

# ============================================================
# EMAIL PARSING FUNCTIONS
# ============================================================

def parse_raw_email(raw_email: str) -> Dict:
    try:
        msg = email.message_from_string(raw_email, policy=policy.default)
        header_dict = {"subject": msg.get("Subject", ""), "from": msg.get("From", "")}
        
        body_text = ""
        html_content = ""
        
        for part in msg.walk():
            if part.is_multipart(): continue
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            if payload:
                if ctype == "text/plain":
                    body_text += payload.decode('utf-8', errors='ignore') + "\n"
                elif ctype == "text/html":
                    html_content += payload.decode('utf-8', errors='ignore') + "\n"

        urls = []
        is_spoofed = False  
        
        if body_text:
            urls.extend(re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', body_text))

        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            for a in soup.find_all('a', href=True):
                href = a['href'].strip().strip('\'"')
                text = a.get_text(strip=True)
                urls.append(href)
                
                if re.search(r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', text):
                    try:
                        clean_text = text.strip()
                        if not clean_text.startswith(('http://', 'https://')):
                            clean_text = "http://" + clean_text
                            
                        text_domain = urlparse(clean_text).netloc.replace("www.", "").lower()
                        href_domain = urlparse(href).netloc.replace("www.", "").lower()
                        
                        if text_domain and href_domain and text_domain != href_domain:
                            is_spoofed = True
                    except Exception:
                        pass
            
        clean_urls = []
        for u in urls:
            u = u.strip().strip('\'"')
            if u.startswith('mailto:'): continue
            if u.startswith('//'): u = 'https:' + u
            if u.startswith('http'): clean_urls.append(u)

        return {
            "header_details": header_dict,
            "text": body_text.strip(),
            "html": html_content.strip(),
            "urls": list(set(clean_urls)),
            "is_spoofed": is_spoofed, 
            "parsing_status": "success"
        }
    except Exception as e:
        return {"parsing_status": "error", "error": str(e)}

# ============================================================
# PREDICTION FUNCTIONS
# ============================================================

def predict_text_bert(text: str) -> Dict:
    if not bert_model: return {"model": "BERT", "error": "Model not loaded"}
    try:
        clean_text = " ".join(text.split())[:1000] 
        inputs = tokenizer(clean_text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = bert_model(**inputs)
        
        temperature = 2.0 
        logits = outputs.logits / temperature
        probabilities = F.softmax(logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)
        
        result = "Phishing" if predicted_class.item() == 1 else "Legitimate"
        raw_risk = confidence.item() if result == "Phishing" else (1.0 - confidence.item())

        return {"model": "BERT", "prediction": result, "confidence": round(float(confidence.item()), 4), "raw_risk": float(raw_risk)}
    except Exception as e:
        return {"model": "BERT", "error": str(e)}

def predict_url_features(urls: List[str]) -> Dict:
    if not url_model: return {"model": "URL", "error": "Model not loaded"}
    try:
        if not urls: return {"model": "URL", "prediction": "Legitimate", "confidence": 0.0, "raw_risk": 0.0}

        domain_counts = Counter([urlparse(u).netloc.lower() for u in urls])
        all_results = []
        
        TRUSTED_DOMAINS = {
            'youtube.com', 'pwc.com.my', 'github.com', 'linkedin.com', 
            'google.com', 'microsoft.com', 'tryhackme.com', 
            'customeriomail.com', 'customer.io', 'discord.com', 
            'twitter.com', 'instagram.com', 'facebook.com', 't.co',
            'taylors.edu.my'
        }
        
        for url in urls:
            ext = tldextract.extract(url)
            registered_domain = ext.registered_domain.lower()
            
            # 🚀 FIX: Ignore malformed URLs (like http://) that lack a registered domain
            if not registered_domain:
                continue

            features_dict = URLFeatures(url).get_features()
            features_list = [list(features_dict.values())]
            
            prediction = url_model.predict(features_list)[0]
            probabilities = url_model.predict_proba(features_list)[0]
            confidence = float(max(probabilities))
            risk = confidence if prediction == 1 else (1.0 - confidence)

            if registered_domain in TRUSTED_DOMAINS:
                risk = min(risk, 0.01) 
            elif domain_counts[urlparse(url).netloc.lower()] >= 3:
                risk = risk * 0.4
            
            all_results.append(risk)
        
        if not all_results:
             return {"model": "URL", "prediction": "Legitimate", "confidence": 1.0, "raw_risk": 0.0}

        max_risk = max(all_results)
        final_prediction = "Phishing" if max_risk >= 0.5 else "Legitimate"
        display_confidence = max_risk if final_prediction == "Phishing" else (1.0 - max_risk)
            
        return {"model": "URL", "prediction": final_prediction, "confidence": round(float(display_confidence), 4), "raw_risk": max_risk, "urls_analyzed": len(urls)}
    except Exception as e:
        return {"model": "URL", "error": str(e)}

def predict_html_features(html_text: str) -> Dict:
    if not html_model: return {"model": "HTML", "error": "Model not loaded"}
    try:
        if not html_text.strip(): return {"model": "HTML", "prediction": "No HTML", "confidence": 0.0, "raw_risk": 0.0}
        features_dict = HTMLFeatures(html_text).get_features()
        prediction = html_model.predict([list(features_dict.values())])[0]
        confidence = float(max(html_model.predict_proba([list(features_dict.values())])[0]))
        
        result = "Phishing" if int(prediction) == 1 else "Legitimate"
        raw_risk = confidence if result == "Phishing" else (1.0 - confidence)
        
        return {"model": "HTML", "prediction": result, "confidence": round(confidence, 4), "raw_risk": float(raw_risk)}
    except Exception as e:
        return {"model": "HTML", "error": str(e)}

# ============================================================
# CONFIDENCE-WEIGHTED ENSEMBLE SCORING
# ============================================================

def calculate_total_phishing_score(predictions: List[Dict], is_spoofed: bool = False) -> Dict:
    scores = {p['model']: p for p in predictions if "error" not in p}
    if not scores: return {"total_score": 0.0, "final_prediction": "Unable to predict"}

    models = ['URL', 'BERT', 'HTML']
    risks = {}
    confidences = {}

    print("\n--- 📊 ENSEMBLE DATA LOG ---")
    for m in models:
        r = scores[m].get('raw_risk', 0.5) if m in scores else 0.5
        risks[m] = r
        conf = abs(r - 0.5) * 1.2 
        confidences[m] = conf
        print(f"[{m}] Risk: {r:.4f} | Conf: {conf:.4f}")

    # Rebalanced base weights to allow BERT a stronger voice in clear-cut cases
    base_weights = {'URL': 0.45, 'BERT': 0.35, 'HTML': 0.20}
    dynamic_weights = {}
    total_dynamic_weight = 0.0

    for m in models:
        w = base_weights[m] * (confidences[m] + 0.1) 
        
        # Dampener: Mutes BERT's weight ONLY if the URL is verified safe
        if m == 'BERT':
            url_r = risks.get('URL', 0.5)
            w = w * (0.1 + (0.9 * url_r))
            
        dynamic_weights[m] = w
        total_dynamic_weight += w

    final_risk = 0.0
    for m in models:
        normalized_w = dynamic_weights[m] / total_dynamic_weight
        contribution = risks[m] * normalized_w
        final_risk += contribution
        print(f"[{m}] Weight: {normalized_w:.4f} | Impact: {contribution:.4f}")

    if is_spoofed:
        print(f"SPOOF_FLAG: TRUE | Pre-Adj Risk: {final_risk:.4f}")
        final_risk = final_risk + (1.0 - final_risk) * 0.90 

    print(f"RESULT_RISK: {final_risk:.4f}")
    print("---------------------------\n")

    final_prediction = "Phishing" if final_risk >= 0.5 else "Legitimate"
    display_confidence = final_risk if final_prediction == "Phishing" else (1.0 - final_risk)

    return {
        "total_score": round(float(display_confidence), 4),
        "final_prediction": final_prediction,
        "active_gate": "Ensemble" if not is_spoofed else "Spoof_Penalty",
        "raw_risk_data": {m: round(risks[m], 4) for m in models}
    }

# ============================================================
# API ENDPOINT
# ============================================================

@app.post("/parse-and-predict")
async def parse_and_predict_endpoint(raw_email: RawEmailInput):
    try:
        parsed_email = parse_raw_email(raw_email.email_content)
        if parsed_email["parsing_status"] == "error":
            raise HTTPException(status_code=400, detail="Parsing failed")
        
        predictions = []
        subject = parsed_email["header_details"].get("subject", "")
        body_text = parsed_email["text"]
        
        if not body_text and parsed_email["html"]:
            body_text = BeautifulSoup(parsed_email["html"], "html.parser").get_text(separator=' ', strip=True)

        combined_text = f"{subject} {body_text}".strip()
        
        if combined_text: predictions.append(predict_text_bert(combined_text))
        if parsed_email["urls"]: predictions.append(predict_url_features(parsed_email["urls"]))
        if parsed_email["html"]: predictions.append(predict_html_features(parsed_email["html"]))
        
        total_result = calculate_total_phishing_score(predictions, parsed_email.get("is_spoofed", False))
        
        return {"individual_predictions": predictions, "combined_analysis": total_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))