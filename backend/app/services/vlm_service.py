import os
import json
from PIL import Image
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Literal
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


# =====================================================================
# Strict Pydantic Schema for Guaranteed VLM Output Structure
# =====================================================================
class VLMAnalysisSchema(BaseModel):
    damage_description: str = Field(
        description="A precise 2-3 sentence visual summary describing structural, panel, or glass damage."
    )
    detected_parts: List[str] = Field(
        description="List of damaged vehicle components (e.g. ['Windshield', 'A-Pillar', 'Front Bumper', 'Right Headlight'])."
    )
    severity: Literal["minor", "moderate", "severe", "total_loss"] = Field(
        description="Severity category: minor (< ₹15,000), moderate (< ₹60,000), severe (> ₹1,00,000), total_loss (structural/roof collapse)."
    )
    is_genuine: bool = Field(
        description="True if authentic camera capture; False if stock photo, screen photo, or digitally manipulated."
    )
    number_plate: str = Field(
        description="Exact registration plate text if visible anywhere (e.g., 'TN-01-AM-6142'), otherwise 'NOT_VISIBLE'."
    )
    detected_car_model: str = Field(
        description="Exact vehicle make/model (e.g., 'Hyundai i20', 'Maruti Suzuki Swift'). If unidentifiable, return 'NOT_VISIBLE'."
    )
    estimated_cost_min: float = Field(
        description="Realistic minimum repair/replacement cost in INR."
    )
    estimated_cost_max: float = Field(
        description="Realistic maximum repair/replacement cost in INR."
    )
    is_indian_environment: bool = Field(
        description="True if the vehicle/roadway environment matches Indian infrastructure (RHD steering, Indian road markings, Indian license plates, Indian signage). False if non-Indian elements are detected."
    )
    geographic_incongruity_detected: bool = Field(
        description="True if non-Indian scene markers (e.g., solid double-yellow center lines, left-hand drive vehicle, foreign signage/language, US state plates) are present."
    )
    geographic_incongruity_reason: str = Field(
        description="Specific non-Indian scene indicators found (e.g., 'Solid double-yellow center line and Left-Hand Drive steering wheel'), or 'NONE'."
    )


# =====================================================================
# VLM Damage Analysis Function
# =====================================================================
def analyze_damage_with_vlm(image_path: str) -> dict:
    """
    Multimodal damage assessment, license plate extraction, Indian cost estimation, and scene geography audit.
    """
    if not os.path.exists(image_path) or not client:
        print("⚠️ VLM Notice: Missing image path or GEMINI_API_KEY.")
        return {
            "success": False,
            "vlm_damage_description": "VLM analysis unavailable (missing image or API key).",
            "vlm_severity": "unknown",
            "vlm_is_genuine": True,
            "vlm_fraud_indicators": [],
            "vlm_number_plate": "NOT_VISIBLE",
            "vlm_detected_model": "Car model not detected — Please upload clearer images",
            "vlm_estimated_cost_min": 0.0,
            "vlm_estimated_cost_max": 0.0,
            "vlm_is_indian_environment": True,
            "vlm_geographic_incongruity": False,
            "vlm_geographic_incongruity_reason": "NONE"
        }

    try:
        # Convert and sanitize image
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        prompt = """
        You are a senior automotive insurance surveyor in India.
        Carefully examine this damaged vehicle photograph and adhere strictly to these rules:

        1. LICENSE PLATE EXTRACTION:
           - Check the front bumper, rear bumper, windshield stickers, and registration brackets.
           - If an Indian registration plate is visible (e.g., TN-01-AM-6142, MH-12-DE-1433), extract the exact alphanumeric string.
           - Only return 'NOT_VISIBLE' if the plate is completely obscured, cropped out, or illegible.

        2. SEVERITY & DAMAGE GRADING (INDIAN MARKET BENCHMARKS):
           - 'minor': Surface scratches, minor bumper scuffs, small paint chips (Cost: ₹3,000 - ₹15,000).
           - 'moderate': Dent on 1-2 panels, cracked headlamp/taillamp, replaceable plastic bumper (Cost: ₹15,000 - ₹60,000).
           - 'severe': Shattered laminated windscreen, multiple crushed metal panels, A/B pillar deformation, suspension/wheel damage (Cost: ₹80,000 - ₹2,50,000).
           - 'total_loss': Roof crush/rollover, severe chassis frame destruction, engine compartment collapse, flood submersion (Cost: ₹2,50,000 - ₹6,00,000+).

        3. VEHICLE IDENTIFICATION:
           - Identify the make/model from body contours, badges, and grille (e.g., 'Hyundai i10', 'Maruti Suzuki Swift', 'Honda City').

        4. IMAGE GENUINENESS:
           - Flag (is_genuine = false) if the photo exhibits screen moiré patterns, stock photo watermarks, or artificial digital alterations.

        5. GEOGRAPHIC SCENE & ROADWAY ENVIRONMENT AUDIT (ZERO-LATENCY FORENSICS):
           - Inspect background architecture, lane markings, vehicle steering wheel placement, license plate format, and signage.
           - Check for non-Indian infrastructure markers:
             a) Road lane markings: Solid double-yellow center lines (standard in North America/Europe, absent on Indian roads).
             b) Vehicle configuration: Left-Hand Drive (LHD) steering wheel (driver seated on the left side).
             c) Signage & Architecture: Foreign language speed limit/traffic signs (e.g. 'SPEED LIMIT 65', 'STOP' in US typography), foreign street/store signs, US state license plates.
           - Set is_indian_environment = False and geographic_incongruity_detected = True if any non-Indian markers are found.
        """

        # Call Gemini with Structured JSON Output Enforcement
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VLMAnalysisSchema,
                temperature=0.1  # Low temperature for deterministic evaluation
            )
        )

        result = json.loads(response.text)

        # Clean vehicle model text
        raw_model = str(result.get("detected_car_model", "NOT_VISIBLE")).strip()
        if raw_model.upper() in ["NOT_VISIBLE", "UNKNOWN", "NOT DETECTED", "NONE", "UNCLEAR"]:
            formatted_model = "Car model not detected — Please upload clearer images"
        else:
            formatted_model = raw_model

        return {
            "success": True,
            "vlm_damage_description": str(result.get("damage_description", "Vehicle damage observed.")),
            "vlm_severity": str(result.get("severity", "moderate")).lower(),
            "vlm_is_genuine": bool(result.get("is_genuine", True)),
            "vlm_fraud_indicators": [] if result.get("is_genuine", True) else ["Stock / Non-genuine photo pattern detected"],
            "vlm_number_plate": str(result.get("number_plate", "NOT_VISIBLE")),
            "vlm_detected_model": formatted_model,
            "vlm_estimated_cost_min": float(result.get("estimated_cost_min", 15000.0)),
            "vlm_estimated_cost_max": float(result.get("estimated_cost_max", 45000.0)),
            "vlm_is_indian_environment": bool(result.get("is_indian_environment", True)),
            "vlm_geographic_incongruity": bool(result.get("geographic_incongruity_detected", False)),
            "vlm_geographic_incongruity_reason": str(result.get("geographic_incongruity_reason", "NONE"))
        }

    except Exception as e:
        print(f"❌ VLM Processing Exception: {e}")
        return {
            "success": False,
            "vlm_damage_description": "Vehicle structural and body impact observed.",
            "vlm_severity": "moderate",
            "vlm_is_genuine": True,
            "vlm_fraud_indicators": [],
            "vlm_number_plate": "NOT_VISIBLE",
            "vlm_detected_model": "Car model not detected — Please upload clearer images",
            "vlm_estimated_cost_min": 15000.0,
            "vlm_estimated_cost_max": 45000.0,
            "vlm_is_indian_environment": True,
            "vlm_geographic_incongruity": False,
            "vlm_geographic_incongruity_reason": "NONE"
        }

    except Exception as e:
        print(f"❌ VLM Processing Exception: {e}")
        return {
            "success": False,
            "vlm_damage_description": "Vehicle structural and body impact observed.",
            "vlm_severity": "moderate",
            "vlm_is_genuine": True,
            "vlm_fraud_indicators": [],
            "vlm_number_plate": "NOT_VISIBLE",
            "vlm_detected_model": "Car model not detected — Please upload clearer images",
            "vlm_estimated_cost_min": 15000.0,
            "vlm_estimated_cost_max": 45000.0
        }


# =====================================================================
# Executive Claim Summary Generator
# =====================================================================
def generate_claim_summary_llm(claim_data: dict) -> str:
    """
    LLM generates an executive summary with risk analysis for the claim agent.
    """
    if not client:
        return f"Claim for {claim_data.get('car_model', 'Vehicle')} submitted by {claim_data.get('customer_name', 'Customer')}."

    try:
        fraud_score = float(claim_data.get('fraud_score', 0.0))
        fraud_pct = int(round(fraud_score * 100))
        mismatch_reason = claim_data.get('image_fraud_reason', '')

        # Determine risk tier and final action recommendation
        if fraud_score >= 0.70 or mismatch_reason:
            risk_tier = "CRITICAL FRAUD RISK"
            required_recommendation = "Investigate" if fraud_score < 0.85 else "Reject"
        elif fraud_score >= 0.35:
            risk_tier = "MODERATE FRAUD RISK"
            required_recommendation = "Investigate"
        else:
            risk_tier = "LOW RISK"
            required_recommendation = "Approve"

        prompt = f"""
        You are an AI Insurance Fraud Analyst drafting an executive summary for an insurance agent.

        CLAIM DETAILS:
        - Policyholder: {claim_data.get('customer_name')}
        - Claimed Vehicle: {claim_data.get('car_model')}
        - Claimed Amount: ₹{claim_data.get('claim_amount')}
        - AI Fraud Risk Score: {fraud_pct}% ({risk_tier})
        - Risk Factors / Flags: {mismatch_reason if mismatch_reason else 'None'}
        - Visual Damage Assessment: {claim_data.get('vlm_damage_description')}
        - Data Consistency Status: {claim_data.get('consistency_status')}

        INSTRUCTIONS:
        1. Write a 2 to 3 sentence concise executive appraisal.
        2. Mention the AI Fraud Risk ({fraud_pct}%) and any detected inconsistencies (e.g. plate mismatch, missing metadata, high repair disparity).
        3. End the final sentence with the exact bold recommendation: **{required_recommendation}**
        """

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text.strip()

    except Exception as e:
        print(f"❌ LLM Summary Error: {e}")
        return "Executive summary generation skipped."