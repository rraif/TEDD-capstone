from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import BertForSequenceClassification, BertTokenizer
import torch
import torch.nn.functional as F
import os
import logging

logging.basicConfig(level=logging.INFO)

MODEL_PATH = "./tedd_bert_final" 


try:
    print(f"Loading model from {MODEL_PATH}...")
    tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
    model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval() # Set to evaluation mode (faster)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Did you unzip the folder? Is the path correct?")

app = FastAPI()

class TextInput(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the TEDD Phishing Detection API!"}

@app.post("/predict")
async def predict_endpoint(item: TextInput):
    text = item.text
    logging.info(f"Received input: {text}")

    # --- 3. ACTUAL PREDICTION LOGIC ---
    try:
        # A. Tokenize (Preprocess)
        inputs = tokenizer(
            text,
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
        )

        # B. Inference (Run Model)
        with torch.no_grad(): # Disable gradient calculation for speed
            outputs = model(**inputs)
        
        # C. Post-processing (Convert numbers to "Phishing" or "Safe")
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)

        # Map 0/1 to labels (Check your Colab to confirm which is which!)
        # Assuming: 0 = Safe, 1 = Phishing
        labels = ["Legitimate", "Phishing"]
        result = labels[predicted_class.item()]

        logging.info(f"Predicted result: {result}")
        
        return {
            "text": text, 
            "prediction": result,
            "confidence": round(float(confidence.item()), 4)
        }

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))