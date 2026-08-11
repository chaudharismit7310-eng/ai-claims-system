import os
import json
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Initialize Gemini Client with API key
api_key = os.getenv("GEMINI_API_KEY", "")
client = None

if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("⚠️ WARNING: GEMINI_API_KEY is missing or not loaded from .env!")

# Recommended fast multimodal model
MODEL_ID = "gemini-2.5-flash"


def analyze_damage_with_vlm(image_path: str) -> dict:
    """
    VLM analyzes car damage image, detects exact car model, and extracts visual insights.
    """
    if not os.path.exists(image_path) or not client:
        print("⚠️ VLM Notice: Missing image path or GEMINI_API_KEY.")
        return {
            "success": False,
            "vlm_damage_description": "VLM analysis unavailable (missing image or API key).",
            "vlm_severity": "unknown",
            "vlm_is_genuine": True,
            "vlm_fraud_indicators": [],
            "vlm_number_plate": "not_visible",
            "vlm_detected_model": "Car model not detected — Please upload clearer images",
            "vlm_estimated_cost_min": 0.0,
            "vlm_estimated_cost_max": 0.0
        }

    try:
        # Convert image to RGB
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        prompt = """
        You are an expert automotive damage appraiser.
        Analyze this vehicle damage photo carefully.
        
        Respond with ONLY a JSON object with these exact keys:
        - damage_description: A detailed 2-sentence visual summary of observed damage.
        - severity: one of "minor", "moderate", "severe", "total_loss"
        - is_genuine: boolean true/false (whether image looks real vs AI-generated or stock photo)
        - number_plate: text of license plate if clearly visible, else "NOT_VISIBLE"
        - detected_car_model: Identify the precise vehicle make and model (e.g. "Honda City", "Maruti Suzuki Ertiga", "Toyota Camry"). IMPORTANT: If the photo is too zoomed in, cropped, or damaged to clearly identify the car model, return "NOT_VISIBLE".
        - estimated_cost_min: estimated minimum repair cost in INR (number)
        - estimated_cost_max: estimated maximum repair cost in INR (number)
        """

        # Call Gemini using google-genai SDK
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        result = json.loads(response.text)

        # Parse detected model cleanly
        raw_model = str(result.get("detected_car_model", "NOT_VISIBLE")).strip()
        if raw_model.upper() in ["NOT_VISIBLE", "UNKNOWN", "NOT DETECTED", "NONE", "UNCLEAR"]:
            formatted_model = "Car model not detected — Please upload clearer images"
        else:
            formatted_model = raw_model

        return {
            "success": True,
            "vlm_damage_description": str(result.get("damage_description", "Vehicle damage observed.")),
            "vlm_severity": str(result.get("severity", "moderate")),
            "vlm_is_genuine": bool(result.get("is_genuine", True)),
            "vlm_fraud_indicators": [],
            "vlm_number_plate": str(result.get("number_plate", "NOT_VISIBLE")),
            "vlm_detected_model": formatted_model,
            "vlm_estimated_cost_min": float(result.get("estimated_cost_min", 10000.0)),
            "vlm_estimated_cost_max": float(result.get("estimated_cost_max", 25000.0))
        }

    except Exception as e:
        print(f"❌ VLM Processing Exception: {e}")
        return {
            "success": False,
            "vlm_damage_description": "Front bumper and vehicle body impact observed.",
            "vlm_severity": "moderate",
            "vlm_is_genuine": True,
            "vlm_fraud_indicators": [],
            "vlm_number_plate": "NOT_VISIBLE",
            "vlm_detected_model": "Car model not detected — Please upload clearer images",
            "vlm_estimated_cost_min": 10000.0,
            "vlm_estimated_cost_max": 25000.0
        }


def generate_claim_summary_llm(claim_data: dict) -> str:
    """
    LLM generates a precise executive summary for the insurance agent.
    """
    if not client:
        return f"Claim for {claim_data.get('car_model', 'Vehicle')} submitted by {claim_data.get('customer_name', 'Customer')}."

    try:
        fraud_score = float(claim_data.get('fraud_score', 0.0))
        fraud_pct = int(round(fraud_score * 100))
        mismatch_reason = claim_data.get('image_fraud_reason', '')

        # Calculate exact risk tier and required recommendation in Python
        if fraud_score >= 0.7 or mismatch_reason:
            risk_tier = "CRITICAL FRAUD RISK"
            required_recommendation = "Investigate" if fraud_score < 0.85 else "Reject"
        elif fraud_score >= 0.35:
            risk_tier = "MODERATE FRAUD RISK"
            required_recommendation = "Investigate"
        else:
            risk_tier = "LOW RISK"
            required_recommendation = "Approve"

        prompt = f"""
        You are an AI Insurance Fraud Analyst drafting a 3-sentence executive summary for an insurance claim agent.

        CLAIM DETAILS:
        - Customer: {claim_data.get('customer_name')}
        - Claimed Vehicle: {claim_data.get('car_model')}
        - Claim Amount: ₹{claim_data.get('claim_amount')}
        - AI Fraud Risk Score: {fraud_pct}% ({risk_tier})
        - Detected Risk Factors / Mismatches: {mismatch_reason if mismatch_reason else 'None'}
        - Visual Analysis: {claim_data.get('vlm_damage_description')}
        - Data Consistency: {claim_data.get('consistency_status')}

        INSTRUCTIONS:
        1. Summarize the claim details and visual damage observations.
        2. State the AI Fraud Risk percentage ({fraud_pct}%) and explicitly highlight any detected mismatches, unreadable photos, or forgery warnings if present.
        3. You MUST end your 3-sentence summary with the exact bold recommendation: **{required_recommendation}**
        """

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print(f"❌ LLM Summary Error: {e}")
        return "Executive summary generation skipped."