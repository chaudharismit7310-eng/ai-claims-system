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

def create_image_with_exif(lat=18.5204, lon=73.8567):
    img = Image.new('RGB', (400, 300), color=(50, 200, 50))
    exif = img.getexif()
    gps_ifd = exif.get_ifd(34853)
    gps_ifd[1] = 'N' if lat >= 0 else 'S'
    abs_lat = abs(lat)
    d_lat = int(abs_lat)
    m_lat = int((abs_lat - d_lat) * 60)
    s_lat = round(((abs_lat - d_lat) * 60 - m_lat) * 60, 2)
    gps_ifd[2] = (float(d_lat), float(m_lat), float(s_lat))

    gps_ifd[3] = 'E' if lon >= 0 else 'W'
    abs_lon = abs(lon)
    d_lon = int(abs_lon)
    m_lon = int((abs_lon - d_lon) * 60)
    s_lon = round(((abs_lon - d_lon) * 60 - m_lon) * 60, 2)
    gps_ifd[4] = (float(d_lon), float(m_lon), float(s_lon))

    buf = io.BytesIO()
    img.save(buf, format='JPEG', exif=exif)
    buf.seek(0)
    return buf

mock_vlm_standard = {
    "success": True,
    "vlm_damage_description": "Front bumper scuff observed.",
    "vlm_severity": "minor",
    "vlm_is_genuine": True,
    "vlm_fraud_indicators": [],
    "vlm_number_plate": "MH01AB1111",
    "vlm_detected_model": "Honda City",
    "vlm_estimated_cost_min": 5000.0,
    "vlm_estimated_cost_max": 15000.0,
    "vlm_is_indian_environment": True,
    "vlm_geographic_incongruity": False,
    "vlm_geographic_incongruity_reason": "NONE"
}

mock_vlm_incongruity = {
    "success": True,
    "vlm_damage_description": "Front structural impact and bumper damage.",
    "vlm_severity": "severe",
    "vlm_is_genuine": True,
    "vlm_fraud_indicators": [],
    "vlm_number_plate": "MH01AB3333",
    "vlm_detected_model": "Honda City",
    "vlm_estimated_cost_min": 25000.0,
    "vlm_estimated_cost_max": 50000.0,
    "vlm_is_indian_environment": False,
    "vlm_geographic_incongruity": True,
    "vlm_geographic_incongruity_reason": "US-style solid double-yellow center dividers and LHD steering configuration detected."
}

def run_tests():
    print("======================================================================")
    print("🚀 AUTOMATED INTEGRATION TESTS: TELEMETRY DECOUPLING & VLM INCONGRUITY")
    print("======================================================================\n")

    # Patch heavy external calls to run in-memory test suite at lightning speed
    with patch("app.routes.claim_routes.analyze_damage_with_vlm", return_value=mock_vlm_standard), \
         patch("app.routes.claim_routes.extract_number_plate", return_value={"detected_plate": {"plate": "MH01AB1111", "confidence": 0.9}, "plate_found": True}):

        # ------------------------------------------------------------------
        # TEST CASE 1: EXIF Metadata Stripped (Web/Stock Photo Simulation)
        # ------------------------------------------------------------------
        print("▶️ TEST CASE 1: EXIF Metadata Stripped (Web/Stock Photo Simulation)...")
        img_no_exif = create_image_without_exif()

        form_data_1 = {
            "customer_name": "Stripped Test User",
            "car_model": "Honda City",
            "vehicle_number": "MH01AB1111",
            "city": "Mumbai",
            "policy_type": "comprehensive",
            "claim_amount": "35000.0",
            "description": "Scratches and dent on front bumper while driving in Mumbai.",
            "is_live_capture": "false",
            "device_latitude": "19.2403",
            "device_longitude": "73.1305",
            "capture_timestamp": "2026-09-28 15:30:00 UTC"
        }

        files_1 = [("files", ("damage_no_exif.jpg", img_no_exif, "image/jpeg"))]

        res_1 = client.post("/claims/submit-claim", data=form_data_1, files=files_1)
        print(f"   Response Code: {res_1.status_code}")
        assert res_1.status_code in [200, 201], f"Expected 200/201, got {res_1.status_code}: {res_1.text}"

        claim_1 = res_1.json()
        print(f"   Exif GPS Status: {claim_1.get('exif_gps_status')}")
        print(f"   Photo Capture Lat/Lon: {claim_1.get('photo_capture_lat')}, {claim_1.get('photo_capture_lon')}")
        print(f"   Submission Device Lat/Lon: {claim_1.get('submission_device_lat')}, {claim_1.get('submission_device_lon')}")
        print(f"   AI Decision: {claim_1.get('ai_decision')}")

        assert claim_1.get("exif_gps_status") == "METADATA_STRIPPED", "Expected status 'METADATA_STRIPPED'"
        assert claim_1.get("photo_capture_lat") is None, "Expected photo_capture_lat to be None (decoupled from device GPS)"
        assert claim_1.get("photo_capture_lon") is None, "Expected photo_capture_lon to be None (decoupled from device GPS)"
        assert claim_1.get("submission_device_lat") == 19.2403, "Expected submission_device_lat == 19.2403"
        assert claim_1.get("submission_device_lon") == 73.1305, "Expected submission_device_lon == 73.1305"

        xai_1 = json.loads(claim_1.get("xai_explanation", "[]"))
        xai_factors_1 = [f.get("factor") for f in xai_1]
        print(f"   XAI Explanation Factors: {xai_factors_1}")
        has_stripped_factor = any("Missing / Stripped Camera EXIF GPS" in f or "Missing Origin Telemetry" in f for f in xai_factors_1)
        assert has_stripped_factor, "Expected XAI factor 'Missing / Stripped Camera EXIF GPS' in breakdown"

        assert claim_1.get("ai_decision") != "approve_suggested", "STP auto-approval must be revoked for stripped EXIF metadata"
        print("   ✅ Test Case 1 PASSED!\n")

        # ------------------------------------------------------------------
        # TEST CASE 2: Injected Native EXIF GPS (Authentic Camera Simulation)
        # ------------------------------------------------------------------
        print("▶️ TEST CASE 2: Injected Native EXIF GPS (Authentic Camera Simulation)...")
        img_with_exif = create_image_with_exif(lat=18.5204, lon=73.8567)

        form_data_2 = {
            "customer_name": "Authentic Test User",
            "car_model": "Honda City",
            "vehicle_number": "MH01AB2222",
            "city": "Pune",
            "policy_type": "comprehensive",
            "claim_amount": "20000.0",
            "description": "Minor side door dent near Pune city.",
            "is_live_capture": "false",
            "device_latitude": "18.5204",
            "device_longitude": "73.8567",
            "capture_timestamp": "2026-09-28 16:00:00 UTC"
        }

        files_2 = [("files", ("damage_with_exif.jpg", img_with_exif, "image/jpeg"))]

        res_2 = client.post("/claims/submit-claim", data=form_data_2, files=files_2)
        print(f"   Response Code: {res_2.status_code}")
        assert res_2.status_code in [200, 201], f"Expected 200/201, got {res_2.status_code}: {res_2.text}"

        claim_2 = res_2.json()
        print(f"   Exif GPS Status: {claim_2.get('exif_gps_status')}")
        print(f"   Photo Capture Lat/Lon: {claim_2.get('photo_capture_lat')}, {claim_2.get('photo_capture_lon')}")

        assert claim_2.get("exif_gps_status") == "HARDWARE_VERIFIED", "Expected status 'HARDWARE_VERIFIED'"
        assert claim_2.get("photo_capture_lat") is not None and abs(claim_2.get("photo_capture_lat") - 18.5204) < 0.01, f"Expected capture_lat ~18.5204, got {claim_2.get('photo_capture_lat')}"
        assert claim_2.get("photo_capture_lon") is not None and abs(claim_2.get("photo_capture_lon") - 73.8567) < 0.01, f"Expected capture_lon ~73.8567, got {claim_2.get('photo_capture_lon')}"

        xai_2 = json.loads(claim_2.get("xai_explanation", "[]"))
        xai_factors_2 = [f.get("factor") for f in xai_2]
        print(f"   XAI Explanation Factors: {xai_factors_2}")
        has_stripped_penalty_2 = any("Missing / Stripped Camera EXIF GPS" in f for f in xai_factors_2)
        assert not has_stripped_penalty_2, "No 'Missing / Stripped Camera EXIF GPS' penalty should exist when EXIF GPS is verified"
        print("   ✅ Test Case 2 PASSED!\n")

    # ------------------------------------------------------------------
    # TEST CASE 3: Mock VLM Geographic Incongruity Flag
    # ------------------------------------------------------------------
    print("▶️ TEST CASE 3: Mock/Simulate VLM Geographic Incongruity Flag...")
    img_foreign = create_image_without_exif()

    form_data_3 = {
        "customer_name": "Foreign Scene Claimant",
        "car_model": "Honda City",
        "vehicle_number": "MH01AB3333",
        "city": "Mumbai",
        "policy_type": "comprehensive",
        "claim_amount": "45000.0",
        "description": "Collision damage on highway.",
        "is_live_capture": "false",
        "device_latitude": "19.0760",
        "device_longitude": "72.8777"
    }

    files_3 = [("files", ("foreign_scene.jpg", img_foreign, "image/jpeg"))]

    with patch("app.routes.claim_routes.analyze_damage_with_vlm", return_value=mock_vlm_incongruity), \
         patch("app.routes.claim_routes.extract_number_plate", return_value={"detected_plate": {"plate": "MH01AB3333", "confidence": 0.9}, "plate_found": True}):
        res_3 = client.post("/claims/submit-claim", data=form_data_3, files=files_3)

    print(f"   Response Code: {res_3.status_code}")
    assert res_3.status_code in [200, 201], f"Expected 200/201, got {res_3.status_code}: {res_3.text}"

    claim_3 = res_3.json()
    print(f"   Geographic Incongruity Flag: {claim_3.get('geographic_incongruity')}")
    print(f"   Incongruity Reason: {claim_3.get('geographic_incongruity_reason')}")
    print(f"   AI Decision: {claim_3.get('ai_decision')}")

    assert claim_3.get("geographic_incongruity") is True, "Expected geographic_incongruity == True"
    assert claim_3.get("ai_decision") == "reject_suggested", f"Expected ai_decision == 'reject_suggested', got {claim_3.get('ai_decision')}"

    xai_3 = json.loads(claim_3.get("xai_explanation", "[]"))
    xai_factors_3 = [f.get("factor") for f in xai_3]
    print(f"   XAI Explanation Factors: {xai_factors_3}")
    has_geo_factor = any("Non-Indian Scene Detected" in f or "Geographic Scene Incongruity" in f for f in xai_factors_3)
    assert has_geo_factor, "Expected XAI factor 'Non-Indian Scene Detected (Geographic Fraud)' in breakdown"

    print("   ✅ Test Case 3 PASSED!\n")

    print("======================================================================")
    print("🎉 ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================\n")

if __name__ == "__main__":
    run_tests()
