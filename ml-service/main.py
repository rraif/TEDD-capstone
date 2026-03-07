from fastapi import FastAPI, HTTPException, Header, Request # 🚀 Added Request
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
from dotenv import load_dotenv
import shap
from groq import Groq
from lime.lime_text import LimeTextExplainer
import numpy as np
import requests 
import json

# Initialize LIME Text Explainer globally
lime_text_explainer = LimeTextExplainer(class_names=['Legitimate', 'Phishing'])

load_dotenv()
logging.basicConfig(level=logging.INFO)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logging.warning("GROQ_API_KEY is missing from environment variables.")
else:
    groq_client = Groq(api_key=GROQ_API_KEY)

BERT_MODEL_PATH = "./tedd_bert_final"
URL_MODEL_PATH = "./URLClassifier.joblib"
HTML_MODEL_PATH = "./HTMLClassifier.joblib"
EXPECTED_KEY = os.environ.get("INTERNAL_API_KEY", "")

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
                href = a.get('href', '').strip().strip('\'"')
                text = a.get_text(strip=True)
                urls.append(href)
                
                clean_text = text.strip().lower()
                
                if ' ' not in clean_text and '.' in clean_text:
                    try: 
                        ext_text = tldextract.extract(clean_text)
                        ext_href = tldextract.extract(href)
                        
                        if ext_text.domain and ext_text.suffix:
                            text_base = f"{ext_text.domain}.{ext_text.suffix}"
                            if ext_href.domain: 
                                href_base = f"{ext_href.domain}.{ext_href.suffix}" if ext_href.suffix else ext_href.domain
                                if text_base != href_base:
                                    print(f"🚩 SPOOF CAUGHT: Visible Text '{text_base}' -> Hidden Link '{href_base}'")
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
# PREDICTION FUNCTIONS (Two-Stage Architecture)
# ============================================================

def predict_text_bert(text: str, run_xai: bool = False) -> Dict:
    if not bert_model: return {"model": "BERT", "error": "Model not loaded"}
    try:
        word_count = len(text.split())
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

        result_dict = {
            "model": "BERT", 
            "prediction": result, 
            "confidence": round(float(confidence.item()), 4), 
            "raw_risk": float(raw_risk), 
            "word_count": word_count
        }

        if run_xai:
            def predictor_for_lime(texts):
                lime_inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
                with torch.no_grad():
                    lime_probs = F.softmax(bert_model(**lime_inputs).logits / temperature, dim=1).numpy()
                return lime_probs

            exp = lime_text_explainer.explain_instance(clean_text, predictor_for_lime, num_features=5, num_samples=500)
            result_dict["lime_explanation"] = [{"word": word, "weight": float(weight)} for word, weight in exp.as_list()]

        return result_dict
    except Exception as e:
        return {"model": "BERT", "error": str(e)}

def predict_url_features(urls: List[str], run_xai: bool = False) -> Dict:
    if not url_model: return {"model": "URL", "error": "Model not loaded"}
    try:
        if not urls: return {"model": "URL", "prediction": "Legitimate", "confidence": 0.0, "raw_risk": 0.0}

        domain_counts = Counter([urlparse(u).netloc.lower() for u in urls])
        unique_domains = len(set([urlparse(u).netloc.lower() for u in urls if urlparse(u).netloc]))
        all_results = []

        max_risk_tracked = -1.0
        riskiest_features_dict = {}
        
        for url in urls:
            features_dict = URLFeatures(url).get_features()
            features_list = [list(features_dict.values())]
            
            prediction = url_model.predict(features_list)[0]
            probabilities = url_model.predict_proba(features_list)[0]
            confidence = float(max(probabilities))
            risk = confidence if prediction == 1 else (1.0 - confidence)

            if domain_counts[urlparse(url).netloc.lower()] >= 3:
                risk = risk * 0.4
            
            all_results.append(risk)

            if risk > max_risk_tracked:
                max_risk_tracked = risk
                riskiest_features_dict = features_dict
        
        if not all_results:
             return {"model": "URL", "prediction": "Legitimate", "confidence": 1.0, "raw_risk": 0.0}

        max_risk = max(all_results)
        final_prediction = "Phishing" if max_risk >= 0.5 else "Legitimate"
        display_confidence = max_risk if final_prediction == "Phishing" else (1.0 - max_risk)

        result_dict = {
            "model": "URL", 
            "prediction": final_prediction, 
            "confidence": round(float(display_confidence), 4), 
            "raw_risk": max_risk, 
            "urls_analyzed": len(urls), 
            "unique_domains": unique_domains,
            "extracted_urls": urls
        }
            
        if run_xai and riskiest_features_dict:
            feature_names = list(riskiest_features_dict.keys())
            feature_values = list(riskiest_features_dict.values())
            
            explainer = shap.TreeExplainer(url_model)
            shap_values = explainer.shap_values(np.array([feature_values]))
            
            if isinstance(shap_values, list):
                instance_shap_values = shap_values[1][0]
            else:
                instance_shap_values = shap_values[0]

            shap_explanation_data = [
                {"feature": feat, "shap_value": float(val)} 
                for feat, val in zip(feature_names, instance_shap_values)
            ]
            shap_explanation_data.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            result_dict["shap_explanation"] = shap_explanation_data[:5]

        return result_dict
    except Exception as e:
        return {"model": "URL", "error": str(e)}

def predict_html_features(html_text: str, run_xai: bool = False) -> Dict:
    if not html_model: return {"model": "HTML", "error": "Model not loaded"}
    try:
        if not html_text.strip(): return {"model": "HTML", "prediction": "No HTML", "confidence": 0.0, "raw_risk": 0.0}
        
        tag_count = len(BeautifulSoup(html_text, "html.parser").find_all()) if html_text.strip() else 0
        features_dict = HTMLFeatures(html_text).get_features()
        feature_names = list(features_dict.keys())
        feature_values = list(features_dict.values())
        
        prediction = html_model.predict([feature_values])[0]
        confidence = float(max(html_model.predict_proba([feature_values])[0]))
        
        result = "Phishing" if int(prediction) == 1 else "Legitimate"
        raw_risk = confidence if result == "Phishing" else (1.0 - confidence)

        result_dict = {
            "model": "HTML", 
            "prediction": result, 
            "confidence": round(confidence, 4), 
            "raw_risk": float(raw_risk), 
            "html_tag_count": tag_count
        }
        
        if run_xai:
            explainer = shap.TreeExplainer(html_model)
            shap_values = explainer.shap_values(np.array([feature_values]))
            
            if isinstance(shap_values, list):
                instance_shap_values = shap_values[1][0]
            else:
                instance_shap_values = shap_values[0]

            shap_explanation_data = [
                {"feature": feat, "shap_value": float(val)} 
                for feat, val in zip(feature_names, instance_shap_values)
            ]
            shap_explanation_data.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            result_dict["shap_explanation"] = shap_explanation_data[:5]
            
        return result_dict
    except Exception as e:
        return {"model": "HTML", "error": str(e)}

# ============================================================
# CONTEXT-AWARE ENSEMBLE SCORING 
# ============================================================

def calculate_total_phishing_score(predictions: List[Dict], is_spoofed: bool = False) -> Dict:
    scores = {p['model']: p for p in predictions if "error" not in p}
    if not scores: return {"total_score": 0.0, "final_prediction": "Unable to predict"}

    models = ['URL', 'BERT', 'HTML']
    risks = {
        'URL': scores.get('URL', {}).get('raw_risk', 0.0), 
        'BERT': scores.get('BERT', {}).get('raw_risk', 0.5), 
        'HTML': scores.get('HTML', {}).get('raw_risk', 0.0)
    }
    
    base_weights = {'URL': 0.40, 'BERT': 0.40, 'HTML': 0.20}
    dynamic_weights = base_weights.copy()

    bert_muted = False
    marketing_email = False

    url_data = scores.get('URL', {})
    url_count = url_data.get('urls_analyzed', 0)
    unique_domains = url_data.get('unique_domains', 0)
    word_count = scores.get('BERT', {}).get('word_count', 0)
    html_tag_count = scores.get('HTML', {}).get('html_tag_count', 0)
    url_list = url_data.get('extracted_urls', [])

    print("\n--- 📊 ENSEMBLE DATA LOG ---")
    print(f"📝 META | Words: {word_count} | URLs: {url_count} (Unique Domains: {unique_domains}) | HTML Tags: {html_tag_count}")
    
    if url_list:
        print(f"🔗 URLs Analyzed: {url_list}")

    is_zero_payload = (url_count == 0 and html_tag_count < 10)
    
    if is_zero_payload:
        print("🚩 HEURISTIC: Zero-Payload detected. Shifting weight to BERT.")
        dynamic_weights = {'URL': 0.05, 'BERT': 0.90, 'HTML': 0.05}
        if risks['BERT'] > 0.40:
             dynamic_weights['BERT'] = 0.95

    # HEURISTICS
    if risks['BERT'] < 0.25 and risks['URL'] > 0.60:
        dynamic_weights['URL'] = dynamic_weights['URL'] * 0.2  

    if risks['URL'] < 0.50 and risks['HTML'] < 0.60 and risks['BERT'] > 0.80:
        dynamic_weights['BERT'] = dynamic_weights['BERT'] * 0.1 
        dynamic_weights['URL'] = dynamic_weights['URL'] * 1.5
        bert_muted = True

    if url_count >= 8 and html_tag_count > 50 and risks['URL'] < 0.60:
        dynamic_weights['HTML'] = dynamic_weights['HTML'] * 0.1 
        dynamic_weights['BERT'] = dynamic_weights['BERT'] * 0.1
        bert_muted = True
        marketing_email = True

    if word_count > 300 and url_count <= 3 and risks['BERT'] > 0.60:
        dynamic_weights['BERT'] = dynamic_weights['BERT'] * 0.5 
        bert_muted = True

    url_str = url_list[0].lower() if url_list else ""
    enterprise_markers = ['/unsubscribe', '/api/', '/v1/', '/v2/', '/preferences', '/opt-out']
    is_enterprise_path = any(marker in url_str for marker in enterprise_markers)

    if url_count <= 2 and is_enterprise_path and risks['HTML'] < 0.25:
        dynamic_weights['URL'] = dynamic_weights['URL'] * 0.2
        dynamic_weights['BERT'] = dynamic_weights['BERT'] * 0.2
        bert_muted = True

    if url_count >= 10 and unique_domains >= 5 and html_tag_count > 100:
        risks['URL'] = min(risks['URL'], 0.20) 
        dynamic_weights['BERT'] = dynamic_weights['BERT'] * 0.05 
        dynamic_weights['HTML'] = dynamic_weights['HTML'] * 0.05 
        bert_muted = True
        marketing_email = True

    # FINAL CALCULATION
    total_dynamic_weight = sum(dynamic_weights.values())
    final_risk = 0.0
    
    for m in models:
        normalized_w = dynamic_weights[m] / total_dynamic_weight
        impact = risks[m] * normalized_w
        final_risk += impact
        print(f"[{m}] Risk: {risks[m]:.4f} | Weight: {normalized_w:.4f} | Impact: {impact:.4f}")

    if is_spoofed and not marketing_email:
        if risks['BERT'] > 0.40 and not bert_muted:
            final_risk = final_risk + (1.0 - final_risk) * 0.90 
        else:
            final_risk = final_risk + (1.0 - final_risk) * 0.15

    print(f"RESULT_RISK: {final_risk:.4f}")
    print("---------------------------\n")

    final_prediction = "Phishing" if final_risk >= 0.5 else "Legitimate"
    display_confidence = final_risk if final_prediction == "Phishing" else (1.0 - final_risk)

    return {
        "total_score": round(float(display_confidence), 4),
        "threat_level": round(float(final_risk), 4),
        "final_prediction": final_prediction,
        "active_gate": "Zero-Payload-Heuristic" if is_zero_payload else "Ensemble",
        "raw_risk_data": {m: round(risks[m], 4) for m in models}
    }

# ============================================================
# API ENDPOINTS
# ============================================================

# 1. The Fast Base Scan
@app.post("/parse-and-predict")
async def parse_and_predict_endpoint(
    request: Request,                   # 🚀 Added Request
    raw_email: RawEmailInput, 
    x_api_key: str = Header(None)
):
    if x_api_key != EXPECTED_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized internal request")
    
    parsed_email = parse_raw_email(raw_email.email_content)
    if parsed_email["parsing_status"] == "error":
        raise HTTPException(status_code=400, detail="Parsing failed")
        
    subject = parsed_email["header_details"].get("subject", "")
    body_text = parsed_email["text"]
    if not body_text and parsed_email["html"]:
        body_text = BeautifulSoup(parsed_email["html"], "html.parser").get_text(separator=' ', strip=True)

    combined_text = f"{subject} {body_text}".strip()
    
    predictions = []
    # Fast scan - no XAI
    if combined_text: predictions.append(predict_text_bert(combined_text))
    if parsed_email["urls"]: predictions.append(predict_url_features(parsed_email["urls"]))
    if parsed_email["html"]: predictions.append(predict_html_features(parsed_email["html"]))
    
    total_result = calculate_total_phishing_score(predictions, parsed_email.get("is_spoofed", False))
    return {"combined_analysis": total_result}

# 2. The Deep XAI Analysis (THE SLOW ENDPOINT)
@app.post("/explain-threat")
async def explain_threat_endpoint(
    request: Request,                   # 🚀 Added Request
    raw_email: RawEmailInput, 
    x_api_key: str = Header(None)
):
    if x_api_key != EXPECTED_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized internal request")
    
    parsed_email = parse_raw_email(raw_email.email_content)
    if parsed_email["parsing_status"] == "error":
        raise HTTPException(status_code=400, detail="Parsing failed")
        
    subject = parsed_email["header_details"].get("subject", "")
    body_text = parsed_email["text"]
    if not body_text and parsed_email["html"]:
        body_text = BeautifulSoup(parsed_email["html"], "html.parser").get_text(separator=' ', strip=True)

    combined_text = f"{subject} {body_text}".strip()
    is_spoofed = parsed_email.get("is_spoofed", False)

    # 🚀 DISCONNECTION CHECK 1: Before expensive LIME/SHAP
    if await request.is_disconnected():
        logging.info("🚀 Client disconnected before XAI logic. Skipping.")
        return {"status": "cancelled"}

    predictions = []
    if combined_text: predictions.append(predict_text_bert(combined_text, run_xai=True))
    if parsed_email["urls"]: predictions.append(predict_url_features(parsed_email["urls"], run_xai=True))
    if parsed_email["html"]: predictions.append(predict_html_features(parsed_email["html"], run_xai=True))
    
    # Grab top phishing words
    bad_words = []
    for p in predictions:
        if p.get("model") == "BERT" and "lime_explanation" in p:
            pos_words = [item for item in p["lime_explanation"] if item["weight"] > 0]
            pos_words.sort(key=lambda x: x["weight"], reverse=True)
            bad_words = [item["word"] for item in pos_words[:3]]

    # 🚀 DISCONNECTION CHECK 2: Before expensive Groq Call
    if await request.is_disconnected():
        logging.info("🚀 Client disconnected before Groq call. Skipping.")
        return {"status": "cancelled"}

    prompt = f"""
    You are a cybersecurity AI explaining a phishing alert to a non-technical user.
    
    EVIDENCE DETECTED:
    - Link Spoofing: {is_spoofed}
    - Suspicious Text Lures: {bad_words}
    
    FORMATTING & CONTENT RULES:
    1. Output a STRICT bulleted list using '- '. Do not write an intro or outro paragraph. Maximum 3 bullets.
    2. Analyze the EVIDENCE provided:
       - If Link Spoofing is True, explain that a visible link is deceptively hiding its true destination. IF FALSE, DO NOT MENTION SPOOFING OR LINKS AT ALL.
       - If Suspicious Text Lures are present, mentally filter out brand names and URL artifacts (like 'roblox', 'google', 'com', 'http'). Name the remaining words and identify the specific psychological tactic the attacker is using (e.g., creating false urgency, posing as an authority, offering a fake reward, or inducing fear).
       - If neither Spoofing nor Text Lures are present, explain that the email's hidden code and structure matched known malicious patterns.
    3. Actionable Advice: The final bullet point MUST start with "Advice: " and provide one sentence telling the user exactly what to do or check based on the specific threats found.
    4. ZERO technical jargon. Do not mention SHAP, LIME, HTML, URLs, models, or weights.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], 
            model="llama-3.3-70b-versatile", 
            max_tokens=300,
            temperature=0.0
        )
        explanation = chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"❌ Error communicating with Groq API: {e}")
        explanation = "- System unable to generate detailed explanation due to API error."
    
    return {
        "human_readable_explanation": explanation,
        "individual_predictions": predictions
    }