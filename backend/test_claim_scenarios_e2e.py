import sys
import os
import io
import json
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

def create_image_without_exif():
    img = Image.new('RGB', (400, 300), color=(200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf


def run_e2e_scenarios():
    print("======================================================================")
    print(" AUTOMATED E2E VERIFICATION SUITE: 3 DECISION SCENARIOS")
    print("======================================================================\n")

    # Patch LLM summary to avoid external Gemini API 503 errors during test execution
    mock_llm_summary = "Automated AI claim evaluation completed for adjuster review."

    # ------------------------------------------------------------------
    # SCENARIO 1: Claim Rejected (High Fraud Risk)
    # ------------------------------------------------------------------
    print("▶️ RUNNING SCENARIO 1: Claim Rejected (High Fraud Risk)...")
    
    mock_vlm_s1 = {
        "success": True,
        "vlm_damage_description": "Minor hairline paint scratch on bumper.",
        "vlm_severity": "minor",
        "vlm_is_genuine": False,
        "vlm_fraud_indicators": ["Stock / Non-genuine photo pattern detected"],
        "vlm_number_plate": "DL 01 C 9999",
        "vlm_detected_model": "Hyundai i20",
        "vlm_estimated_cost_min": 2000.0,
        "vlm_estimated_cost_max": 5000.0,
        "vlm_is_indian_environment": False,
        "vlm_geographic_incongruity": True,
        "vlm_geographic_incongruity_reason": "Non-Indian LHD vehicle and solid double-yellow center dividers detected"
    }

    mock_forensics_s1 = {
        "image_hash": "hash_s1_fraud",
        "ela_score": 0.095,
        "image_fraud_reason": "High ELA compression variance detected",
        "fraud_score_addition": 0.35,
        "exif_fraud_flag": True,
        "ai_fraud_score": 0.85,
        "is_duplicate": False
    }

    mock_exif_s1 = {
        "has_exif_gps": False,
        "capture_lat": None,
        "capture_lon": None,
        "status": "METADATA_STRIPPED"
    }

    mock_damage_s1 = {
        "detections": [{"class": "scratch", "confidence": 0.35}],
        "severity": "minor",
        "max_confidence": 0.35
    }

    img_s1 = create_image_without_exif()

    payload_s1 = {
        "customer_name": "Scenario1_Fraud_User",
        "car_model": "Honda City",
        "vehicle_number": "MH 12 AB 1234",
        "city": "Kolkata",
        "policy_type": "comprehensive",
        "claim_amount": "85000.0",
        "description": "High speed head-on collision on highway causing frame total loss.",
        "is_live_capture": "false",
        "device_latitude": "22.5726",
        "device_longitude": "88.3639"
    }

    files_s1 = [("files", ("fraud_claim.jpg", img_s1, "image/jpeg"))]

    with patch("app.routes.claim_routes.analyze_damage_with_vlm", return_value=mock_vlm_s1), \
         patch("app.routes.claim_routes.extract_number_plate", return_value={"detected_plate": {"plate": "DL 01 C 9999", "confidence": 0.95}, "plate_found": True}), \
         patch("app.routes.claim_routes.complete_image_analysis", return_value=mock_forensics_s1), \
         patch("app.routes.claim_routes.extract_exif_telemetry", return_value=mock_exif_s1), \
         patch("app.routes.claim_routes.detect_damage", return_value=mock_damage_s1), \
         patch("app.routes.claim_routes.generate_claim_summary_llm", return_value=mock_llm_summary):
        
        res_s1 = client.post("/claims/submit-claim", data=payload_s1, files=files_s1)

    print(f"   HTTP Response Code: {res_s1.status_code}")
    assert res_s1.status_code in [200, 201], f"Expected 200/201, got {res_s1.status_code}: {res_s1.text}"

    claim_s1 = res_s1.json()
    print(f"   Claim ID        : #{claim_s1.get('claim_id')}")
    print(f"   Fraud Score     : {claim_s1.get('fraud_score')}")
    print(f"   AI Decision     : {claim_s1.get('ai_decision')}")
    print(f"   Cost Flag       : {claim_s1.get('cost_flag')}")
    print(f"   Risk Level      : {claim_s1.get('risk_level')}")

    assert claim_s1.get("fraud_score") >= 0.70, f"Expected fraud_score >= 0.70, got {claim_s1.get('fraud_score')}"
    assert claim_s1.get("ai_decision") == "reject_suggested", f"Expected ai_decision == 'reject_suggested', got {claim_s1.get('ai_decision')}"
    
    # Check for fraud reasoning tags
    combined_reasoning = str(claim_s1.get("image_fraud_reason", "")) + str(claim_s1.get("xai_explanation", "")) + str(claim_s1.get("ai_reason", ""))
    has_fraud_triggers = any(keyword in combined_reasoning for keyword in ["GEOGRAPHIC_INCONGRUITY", "Mismatch", "Forensic", "Stripped", "Tampered", "High"])
    assert has_fraud_triggers, "Expected fraud reason to cite geographic incongruity, model/plate mismatch, or forensic tampering"

    print("   [OK] SCENARIO 1 PASSED: Claim correctly flagged for REJECTION with High Fraud Risk!\n")

    # ------------------------------------------------------------------
    # SCENARIO 2: Partially Approved (Adjuster Review Required)
    # ------------------------------------------------------------------
    print("▶️ RUNNING SCENARIO 2: Partially Approved (Adjuster Settlement Required)...")

    mock_vlm_s2 = {
        "success": True,
        "vlm_damage_description": "Rear bumper dent and lower panel scuff.",
        "vlm_severity": "moderate",
        "vlm_is_genuine": True,
        "vlm_fraud_indicators": [],
        "vlm_number_plate": "MH.43.D.3193",  # Punctuation format - normalized plate match!
        "vlm_detected_model": "Hyundai Creta",
        "vlm_estimated_cost_min": 18000.0,
        "vlm_estimated_cost_max": 22000.0,
        "vlm_is_indian_environment": True,
        "vlm_geographic_incongruity": False,
        "vlm_geographic_incongruity_reason": "NONE"
    }

    mock_forensics_s2 = {
        "image_hash": "hash_s2_normal",
        "ela_score": 0.015,
        "image_fraud_reason": "",
        "fraud_score_addition": 0.0,
        "exif_fraud_flag": False,
        "ai_fraud_score": 0.05,
        "is_duplicate": False
    }

    mock_exif_s2 = {
        "has_exif_gps": False,
        "capture_lat": None,
        "capture_lon": None,
        "status": "METADATA_STRIPPED"
    }

    mock_damage_s2 = {
        "detections": [
            {"class": "bumper_damage", "confidence": 0.82},
            {"class": "dent", "confidence": 0.75}
        ],
        "severity": "moderate",
        "max_confidence": 0.82
    }

    img_s2 = create_image_without_exif()

    payload_s2 = {
        "customer_name": "Scenario2_Partial_User",
        "car_model": "Hyundai Creta",
        "vehicle_number": "MH 43 D 3193",
        "city": "Thane",
        "policy_type": "comprehensive",
        "claim_amount": "32000.0",
        "description": "Rear bumper dented while reversing out of parking lot in Thane.",
        "is_live_capture": "false",
        "device_latitude": "19.2183",
        "device_longitude": "72.9781",
        "capture_timestamp": "2026-09-29 18:00:00 UTC",
        "is_post_transit": "true"  # Declared post-transit inspection forces adjuster signoff per protocol
    }

    files_s2 = [("files", ("partial_claim.jpg", img_s2, "image/jpeg"))]

    with patch("app.routes.claim_routes.analyze_damage_with_vlm", return_value=mock_vlm_s2), \
         patch("app.routes.claim_routes.extract_number_plate", return_value={"detected_plate": {"plate": "MH.43.D.3193", "confidence": 0.92}, "plate_found": True}), \
         patch("app.routes.claim_routes.complete_image_analysis", return_value=mock_forensics_s2), \
         patch("app.routes.claim_routes.extract_exif_telemetry", return_value=mock_exif_s2), \
         patch("app.routes.claim_routes.detect_damage", return_value=mock_damage_s2), \
         patch("app.routes.claim_routes.generate_claim_summary_llm", return_value=mock_llm_summary):
        
        res_s2 = client.post("/claims/submit-claim", data=payload_s2, files=files_s2)

    print(f"   HTTP Response Code: {res_s2.status_code}")
    assert res_s2.status_code in [200, 201], f"Expected 200/201, got {res_s2.status_code}: {res_s2.text}"

    claim_s2 = res_s2.json()
    print(f"   Claim ID        : #{claim_s2.get('claim_id')}")
    print(f"   Fraud Score     : {claim_s2.get('fraud_score')}")
    print(f"   AI Decision     : {claim_s2.get('ai_decision')}")
    print(f"   Estimated Cost  : ₹{claim_s2.get('estimated_cost'):,.2f}")
    print(f"   Claimed Amount  : ₹{claim_s2.get('claim_amount'):,.2f}")
    print(f"   Cost Flag       : {claim_s2.get('cost_flag')}")

    assert claim_s2.get("fraud_score") < 0.70, f"Expected moderate fraud_score (< 0.70), got {claim_s2.get('fraud_score')}"
    assert claim_s2.get("ai_decision") in ["manual_review_suggested", "partially_approved"], f"Expected manual review decision, got {claim_s2.get('ai_decision')}"
    assert claim_s2.get("cost_flag") in ["Overcharged", "Undercharged", "Fair"], f"Expected valid cost flag, got {claim_s2.get('cost_flag')}"
    assert claim_s2.get("estimated_cost") > 0, "Expected positive estimated repair cost"

    print("   [OK] SCENARIO 2 PASSED: Claim correctly routed to MANUAL REVIEW with calculated repair estimate range!\n")

    # ------------------------------------------------------------------
    # SCENARIO 3: Fully Approved (Straight-Through Processing / STP)
    # ------------------------------------------------------------------
    print("▶️ RUNNING SCENARIO 3: Fully Approved (Straight-Through Processing / STP)...")

    mock_vlm_s3 = {
        "success": True,
        "vlm_damage_description": "Single cracked taillight lens cover.",
        "vlm_severity": "minor",
        "vlm_is_genuine": True,
        "vlm_fraud_indicators": [],
        "vlm_number_plate": "MH 14 EU 5566",
        "vlm_detected_model": "Maruti Swift",
        "vlm_estimated_cost_min": 5000.0,
        "vlm_estimated_cost_max": 7000.0,
        "vlm_is_indian_environment": True,
        "vlm_geographic_incongruity": False,
        "vlm_geographic_incongruity_reason": "NONE"
    }

    mock_forensics_s3 = {
        "image_hash": "hash_s3_clean",
        "ela_score": 0.010,
        "image_fraud_reason": "",
        "fraud_score_addition": 0.0,
        "exif_fraud_flag": False,
        "ai_fraud_score": 0.02,
        "is_duplicate": False
    }

    mock_exif_s3 = {
        "has_exif_gps": True,
        "capture_lat": 18.5204,
        "capture_lon": 73.8567,
        "status": "HARDWARE_VERIFIED"
    }

    mock_damage_s3 = {
        "detections": [{"class": "taillight_damage", "confidence": 0.88}],
        "severity": "minor",
        "max_confidence": 0.88
    }

    img_s3 = create_image_without_exif()

    payload_s3 = {
        "customer_name": "Scenario3_STP_User",
        "car_model": "Maruti Swift",
        "vehicle_number": "MH 14 EU 5566",
        "city": "Pune",
        "policy_type": "comprehensive",
        "claim_amount": "6000.0",
        "description": "Taillight cracked when another vehicle crashed into my parked car in Pune.",
        "is_live_capture": "false",
        "device_latitude": "18.5204",
        "device_longitude": "73.8567",
        "capture_timestamp": "2026-09-29 20:00:00 UTC"
    }

    files_s3 = [("files", ("stp_claim.jpg", img_s3, "image/jpeg"))]

    with patch("app.routes.claim_routes.analyze_damage_with_vlm", return_value=mock_vlm_s3), \
         patch("app.routes.claim_routes.extract_number_plate", return_value={"detected_plate": {"plate": "MH 14 EU 5566", "confidence": 0.96}, "plate_found": True}), \
         patch("app.routes.claim_routes.complete_image_analysis", return_value=mock_forensics_s3), \
         patch("app.routes.claim_routes.extract_exif_telemetry", return_value=mock_exif_s3), \
         patch("app.routes.claim_routes.detect_damage", return_value=mock_damage_s3), \
         patch("app.routes.claim_routes.generate_claim_summary_llm", return_value=mock_llm_summary):
        
        res_s3 = client.post("/claims/submit-claim", data=payload_s3, files=files_s3)

    print(f"   HTTP Response Code: {res_s3.status_code}")
    assert res_s3.status_code in [200, 201], f"Expected 200/201, got {res_s3.status_code}: {res_s3.text}"

    claim_s3 = res_s3.json()
    print(f"   Claim ID        : #{claim_s3.get('claim_id')}")
    print(f"   Fraud Score     : {claim_s3.get('fraud_score')}")
    print(f"   AI Decision     : {claim_s3.get('ai_decision')}")
    print(f"   Estimated Cost  : ₹{claim_s3.get('estimated_cost'):,.2f}")
    print(f"   Claimed Amount  : ₹{claim_s3.get('claim_amount'):,.2f}")
    print(f"   Cost Flag       : {claim_s3.get('cost_flag')}")

    assert claim_s3.get("fraud_score") < 0.30, f"Expected low fraud_score (< 0.30), got {claim_s3.get('fraud_score')}"
    assert claim_s3.get("ai_decision") == "approve_suggested", f"Expected 'approve_suggested', got {claim_s3.get('ai_decision')}"
    assert claim_s3.get("cost_flag") in ["Fair", "Undercharged"], f"Expected 'Fair' or valid cost flag, got {claim_s3.get('cost_flag')}"

    print("   [OK] SCENARIO 3 PASSED: Claim correctly FULLY APPROVED for Straight-Through Processing (STP)!\n")

    print("======================================================================")
    print(" ALL 3 BUSINESS SCENARIOS VERIFIED SUCCESSFULLY & PASSED END-TO-END!")
    print("======================================================================")

if __name__ == "__main__":
    run_e2e_scenarios()
