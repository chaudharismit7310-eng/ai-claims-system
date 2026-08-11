import torch
import numpy as np
from PIL import Image
import os

# Global model
clip_model = None
clip_processor = None
model_loaded = False

def load_clip_model():
    global clip_model, clip_processor, model_loaded
    try:
        from transformers import CLIPProcessor, CLIPModel
        print("Loading CLIP model...")
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model_loaded = True
        print("CLIP model loaded!")
    except Exception as e:
        print(f"CLIP model load failed: {e}")
        model_loaded = False

def analyze_image_with_ai(image_path: str) -> dict:
    """
    AI-based image analysis using CLIP
    Checks if image is:
    1. Real accident photo
    2. Stock/internet photo
    3. AI generated
    4. Screenshot
    """
    global clip_model, clip_processor, model_loaded

    if not model_loaded:
        load_clip_model()

    if not model_loaded:
        return {
            "ai_fraud_score": 0.0,
            "ai_fraud_reason": "AI model not available",
            "is_real_accident": True,
            "confidence": 0.5,
            "labels": {}
        }

    try:
        from transformers import CLIPProcessor, CLIPModel

        image = Image.open(image_path).convert("RGB")

        # Text prompts for classification
        texts = [
            "a real car accident photo taken at the scene",
            "a stock photo or internet image of car damage",
            "a screenshot or edited image",
            "an AI generated image",
            "a genuine insurance claim photo",
            "a fake or manipulated accident photo"
        ]

        inputs = clip_processor(
            text=texts,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = clip_model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).numpy()[0]

        # Map probabilities
        label_probs = {text: float(prob) for text, prob in zip(texts, probs)}

        # Real accident probability
        real_prob = (
            label_probs["a real car accident photo taken at the scene"] +
            label_probs["a genuine insurance claim photo"]
        )

        # Fake probability
        fake_prob = (
            label_probs["a stock photo or internet image of car damage"] +
            label_probs["a screenshot or edited image"] +
            label_probs["an AI generated image"] +
            label_probs["a fake or manipulated accident photo"]
        )

        # Determine result
        ai_fraud_reasons = []
        ai_fraud_score = 0.0

        if label_probs["a stock photo or internet image of car damage"] > 0.25:
            ai_fraud_reasons.append(
                f"AI DETECTED: Image appears to be a stock/internet photo "
                f"({label_probs['a stock photo or internet image of car damage']:.0%} confidence)"
            )
            ai_fraud_score += 0.35

        if label_probs["an AI generated image"] > 0.20:
            ai_fraud_reasons.append(
                f"AI DETECTED: Image may be AI-generated "
                f"({label_probs['an AI generated image']:.0%} confidence)"
            )
            ai_fraud_score += 0.40

        if label_probs["a screenshot or edited image"] > 0.20:
            ai_fraud_reasons.append(
                f"AI DETECTED: Image appears edited or screenshot "
                f"({label_probs['a screenshot or edited image']:.0%} confidence)"
            )
            ai_fraud_score += 0.30

        if label_probs["a fake or manipulated accident photo"] > 0.20:
            ai_fraud_reasons.append(
                f"AI DETECTED: Image may be manipulated "
                f"({label_probs['a fake or manipulated accident photo']:.0%} confidence)"
            )
            ai_fraud_score += 0.35

        is_real = real_prob > fake_prob

        return {
            "ai_fraud_score": round(min(ai_fraud_score, 1.0), 2),
            "ai_fraud_reason": " | ".join(ai_fraud_reasons),
            "is_real_accident": is_real,
            "real_probability": round(real_prob, 2),
            "fake_probability": round(fake_prob, 2),
            "confidence": round(max(real_prob, fake_prob), 2),
            "labels": {k.split(" ")[-1]: round(v, 3) for k, v in label_probs.items()}
        }

    except Exception as e:
        print(f"AI forgery detection error: {e}")
        return {
            "ai_fraud_score": 0.0,
            "ai_fraud_reason": f"Analysis failed: {str(e)}",
            "is_real_accident": True,
            "confidence": 0.5,
            "labels": {}
        }