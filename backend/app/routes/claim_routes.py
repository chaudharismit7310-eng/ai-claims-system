from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException
)
from fastapi.responses import FileResponse
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.claim_model import Claim
from app.models.vehicle_model import Vehicle as VehicleModel
from app.schemas.claim_schema import ClaimResponse, SettlementRequest

# AI Services
from app.ai_models.yolov8_model import detect_damage
from app.services.nlp_analysis import analyze_fault
from app.services.fraud_detection import detect_fraud
from app.services.decision_engine import decide_claim
from app.services.ocr_service import extract_number_plate
from app.services.cost_estimation import estimate_repair_cost
from app.services.image_forensics import complete_image_analysis
from app.services.heatmap_generator import generate_damage_heatmap
from app.services.consistency_checker import check_claim_consistency
from app.services.explainable_ai import generate_explanation
from app.services.pattern_analysis import analyze_claim_patterns
from app.services.video_keyframe_service import process_walkaround_video
from app.services.garage_auditor import audit_garage_estimate
from app.services.vlm_service import analyze_damage_with_vlm, generate_claim_summary_llm
from app.services.exif_service import extract_exif_telemetry

from app.utils.pdf_generator import generate_claim_pdf
from app.utils.plate_normalizer import normalize_plate
from app.auth import decode_token

import shutil
import os
import json
import numpy as np
from datetime import datetime

router = APIRouter(
    prefix="/claims",
    tags=["Claims"]
)

security = HTTPBearer(
    auto_error=False
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =====================================================
# SUBMIT CLAIM
# =====================================================

@router.post(
    "/submit-claim",
    response_model=ClaimResponse
)
async def submit_claim(
    customer_name: str = Form(...),
    car_model: str = Form(...),
    vehicle_number: Optional[str] = Form(None),
    city: str = Form(...),
    policy_type: str = Form(...),
    claim_amount: float = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(...),
    garage_pdf: Optional[UploadFile] = File(None),
    walkaround_video: Optional[UploadFile] = File(None),
    device_latitude: Optional[float] = Form(None),
    device_longitude: Optional[float] = Form(None),
    capture_timestamp: Optional[str] = Form(None),
    is_live_capture: Optional[bool] = Form(False),
    is_post_transit: str = Form("false"),
    incident_location: Optional[str] = Form(None),
    inspection_location: Optional[str] = Form(None),
    transit_reason: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    is_post_transit_bool = is_post_transit.lower() == "true"


    # 1. USER AUTHENTICATION
    user_id = None
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload:
            user_id = payload.get("user_id")

    # 2. SAVE UPLOADED DAMAGE IMAGES
    saved_paths = []
    for uploaded_file in files:
        file_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)
        saved_paths.append(file_path)

    # 3. SAVE GARAGE ESTIMATE PDF & WALKAROUND VIDEO (IF PROVIDED)
    garage_pdf_path = ""
    if garage_pdf and garage_pdf.filename:
        os.makedirs("uploads/garage", exist_ok=True)
        garage_pdf_path = f"uploads/garage/{garage_pdf.filename}"
        with open(garage_pdf_path, "wb") as pdf_buffer:
            shutil.copyfileobj(garage_pdf.file, pdf_buffer)

    walkaround_video_url = ""
    if walkaround_video and walkaround_video.filename:
        ext = os.path.splitext(walkaround_video.filename)[1].lower()
        if ext in ['.mp4', '.mov', '.webm', '.mkv']:
            os.makedirs("uploads/videos", exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            # Replace spaces to avoid issues
            safe_filename = walkaround_video.filename.replace(" ", "_")
            vid_filename = f"vid_{timestamp_str}_{safe_filename}"
            walkaround_video_url = f"uploads/videos/{vid_filename}"
            with open(walkaround_video_url, "wb") as vid_buffer:
                shutil.copyfileobj(walkaround_video.file, vid_buffer)

    # 4. ACTIVE CLAIM CHECK (Filtered by License Plate to avoid same-model vehicle collisions)
    if user_id:
        active_query = db.query(Claim).filter(
            Claim.user_id == user_id,
            Claim.review_status == "awaiting_review"
        )

        if vehicle_number and vehicle_number.strip():
            active_query = active_query.filter(Claim.number_plate == vehicle_number.strip())
        else:
            active_query = active_query.filter(Claim.car_model == car_model.strip())

        active_claim = active_query.first()

        if active_claim:
            raise HTTPException(
                status_code=400,
                detail=f"Active claim #{active_claim.claim_id} already exists for vehicle {vehicle_number or car_model}!"
            )

    main_image = saved_paths[0] if saved_paths else None

    # 5. GEMINI VLM MULTIMODAL ANALYSIS
    vlm_result = {}
    if main_image:
        vlm_result = analyze_damage_with_vlm(main_image)

    # 5.6 DECOUPLED PHOTO CAPTURE VS SUBMISSION DEVICE TELEMETRY
    submission_device_lat = device_latitude
    submission_device_lon = device_longitude
    photo_capture_lat = None
    photo_capture_lon = None
    exif_gps_status = "METADATA_STRIPPED"

    if main_image:
        exif_telemetry = extract_exif_telemetry(main_image)
        if exif_telemetry.get("has_exif_gps"):
            photo_capture_lat = exif_telemetry["capture_lat"]
            photo_capture_lon = exif_telemetry["capture_lon"]
            exif_gps_status = "HARDWARE_VERIFIED"
        else:
            exif_gps_status = "METADATA_STRIPPED"

    # 5.5 AUDIT GARAGE ESTIMATE (IF PROVIDED)
    garage_audit_json_str = None
    if garage_pdf_path:
        ai_cost = vlm_result.get("vlm_estimated_cost_max", 0.0) if vlm_result else 0.0
        audit_result = audit_garage_estimate(garage_pdf_path, car_model, ai_cost)
        if audit_result:
            garage_audit_json_str = json.dumps(audit_result)

    # 6. IMAGE FORENSICS (ELA, Hash Matching, EXIF, Stock Photo Detection)
    image_analysis = {
        "image_hash": "",
        "ela_score": 0.0,
        "image_fraud_reason": "",
        "fraud_score_addition": 0.0,
        "exif_fraud_flag": False,
        "exif_timestamp": ""
    }
    if main_image:
        image_analysis = complete_image_analysis(
            main_image,
            db=db,
            current_claim_id=None
        )

    # 7. YOLOv8 OBJECT & DAMAGE DETECTION
    damage_results = {"detections": [], "severity": "none", "max_confidence": 0.5}
    if main_image:
        damage_results = detect_damage(main_image)

    damage_info = str(damage_results["detections"])

    # 8. DAMAGE HEATMAP GENERATION
    heatmap_path = ""
    if main_image and damage_results["detections"]:
        heatmap_path = generate_damage_heatmap(main_image, damage_results["detections"])

    # 9. OCR LICENSE PLATE RECOGNITION
    plate_info = "not_detected"
    if main_image:
        ocr_result = extract_number_plate(main_image)
        plate_info = (
            ocr_result["detected_plate"]["plate"]
            if ocr_result.get("plate_found")
            else "not_detected"
        )

    # VLM Plate Fallback if OCR missed it
    if plate_info == "not_detected" and vlm_result.get("vlm_number_plate", "NOT_VISIBLE") not in ["NOT_VISIBLE", "not_visible", ""]:
        plate_info = vlm_result.get("vlm_number_plate")

    # Selected Registered Vehicle Number Fallback if photo plate was unreadable
    if plate_info in ["not_detected", "not_visible", "NOT_VISIBLE", ""] and vehicle_number:
        plate_info = vehicle_number

    # 10. NLP INCIDENT FAULT ANALYSIS
    fault_result = analyze_fault(description)
    driver_fault = (fault_result["fault"] == "driver_fault")
    natural_cause = (fault_result["fault"] == "natural")
    damage_conf = (
        damage_results["detections"][0]["confidence"]
        if damage_results["detections"] else 0.5
    )

    # 11. PROFILE QUERY & DYNAMIC RISK BINDING
    past_claims_count = 0
    registered_cars_count = 1
    vehicle_age = 4
    driver_age = 35

    if user_id:
        past_claims_count = db.query(Claim).filter(Claim.user_id == user_id).count()
        user_vehicle_records = db.query(VehicleModel).filter(VehicleModel.user_id == user_id).all()
        registered_cars_count = max(1, len(user_vehicle_records))
        if user_vehicle_records:
            vehicle_age = 4  # Typical active policy lifespan

    # Only flag photo as tampered if confirmed duplicate, high CLIP forgery, or editing software in EXIF
    is_tampered_photo = (
        image_analysis.get("is_duplicate", False) or 
        (image_analysis.get("ai_fraud_score", 0.0) > 0.50) or 
        image_analysis.get("exif_fraud_flag", False)
    )
    final_vlm_is_genuine = bool(vlm_result.get("vlm_is_genuine", True) and not is_tampered_photo)

    fraud_result = detect_fraud(
        damage_confidence=damage_conf,
        driver_fault=driver_fault,
        natural_cause=natural_cause,
        claim_amount=claim_amount,
        previous_claims=past_claims_count,
        driver_age=driver_age,
        vehicle_age=vehicle_age,
        number_of_cars=registered_cars_count,
        image_forgery_score=image_analysis.get("ai_fraud_score", 0.0)
    )

    # Balanced ML probability + forensic penalties
    base_fraud = fraud_result["fraud_score"]
    forensic_addition = 0.0
    if image_analysis.get("is_duplicate"):
        forensic_addition += 0.35
    elif image_analysis.get("ai_fraud_score", 0.0) > 0.45:
        forensic_addition += 0.15
    if image_analysis.get("exif_fraud_flag"):
        forensic_addition += 0.15
    if not final_vlm_is_genuine:
        forensic_addition += 0.10

    fraud_score = min(1.0, round(base_fraud + forensic_addition, 2))

    # 12. CAR MODEL & VEHICLE IDENTITY CROSS-VALIDATION
    mismatch_flags = []

    if user_id:
        user_vehicles = db.query(VehicleModel).filter(VehicleModel.user_id == user_id).all()
        user_vehicle = None

        if vehicle_number:
            norm_form_v_num = normalize_plate(vehicle_number)
            for v in user_vehicles:
                v_num_str = getattr(v, "vehicle_number", None) or getattr(v, "license_plate", None) or ""
                v_num = normalize_plate(v_num_str)
                if v_num and norm_form_v_num and v_num == norm_form_v_num:
                    user_vehicle = v
                    break

        if not user_vehicle and user_vehicles:
            user_vehicle = user_vehicles[0]

        if user_vehicle:
            reg_model = (user_vehicle.car_model or "").lower().strip()
            form_model = (car_model or "").lower().strip()
            photo_detected = vlm_result.get("vlm_detected_model", "")
            photo_model = photo_detected.lower().strip()

            # Check A: Claim form model vs Registered vehicle model
            if reg_model and form_model and reg_model not in form_model and form_model not in reg_model:
                mismatch_flags.append(f"Model Mismatch: Registered '{user_vehicle.car_model}' but claimed '{car_model}'")

            # Check B: Photo car model (Gemini VLM) vs Registered vehicle model
            if "not detected" in photo_model or "not_visible" in photo_model:
                mismatch_flags.append("Photo Model Unclear: Vehicle model not visible in image — Agent should request clearer full-vehicle photos.")
            elif reg_model and photo_model:
                if reg_model not in photo_model and photo_model not in reg_model:
                    mismatch_flags.append(f"Photo Mismatch: Registered '{user_vehicle.car_model}' but photo shows '{photo_detected}'")

            # Check C: Registered License Plate vs Photo Detected Plate
            registered_plate_str = (getattr(user_vehicle, "vehicle_number", None) or getattr(user_vehicle, "license_plate", None) or "")
            reg_plate = normalize_plate(registered_plate_str)
            photo_plate = normalize_plate(plate_info)

            if reg_plate and photo_plate and photo_plate not in ["NOTDETECTED", "NOTVISIBLE"]:
                if reg_plate != photo_plate and reg_plate not in photo_plate and photo_plate not in reg_plate:
                    mismatch_flags.append(f"Plate Mismatch: Registered '{registered_plate_str}' vs Photo Detected '{plate_info}'")

    if mismatch_flags:
        has_real_mismatch = any("Mismatch" in m for m in mismatch_flags)
        if has_real_mismatch:
            fraud_score = min(fraud_score + 0.25, 1.0)
        
        mismatch_msg = " | ".join(mismatch_flags)
        if image_analysis.get("image_fraud_reason"):
            image_analysis["image_fraud_reason"] += f" | 🚨 {mismatch_msg}"
        else:
            image_analysis["image_fraud_reason"] = f"🚨 {mismatch_msg}"

    # 12.5 GEOLOCATION & CITY CONSISTENCY TRIAGE LOGIC
    geo_discrepancy_detected = False
    location_keywords = ["pune", "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "ahmedabad", "surat", "jaipur", "lonavala", "kalyan", "thane", "expressway"]
    desc_lower = (description or "").lower()
    city_lower = (city or "").lower()
    inc_loc_lower = (incident_location or "").lower() if incident_location else ""

    narrative_locs = [loc for loc in location_keywords if loc in desc_lower or loc in inc_loc_lower]
    city_locs = [loc for loc in location_keywords if loc in city_lower]

    if narrative_locs and city_locs:
        if not any(n_loc in city_lower for n_loc in narrative_locs) and not any(c_loc in desc_lower for c_loc in city_locs):
            geo_discrepancy_detected = True
    elif narrative_locs and not city_locs:
        if not any(loc in city_lower for loc in narrative_locs):
            geo_discrepancy_detected = True

    if is_post_transit_bool:
        # Suppress geographic discrepancy penalties per declared safe transit protocol
        geo_discrepancy_detected = False
    else:
        if geo_discrepancy_detected:
            # Undeclared Geographic Discrepancy Penalty (+30% Fraud Risk)
            fraud_score = min(1.0, fraud_score + 0.30)
            discrepancy_msg = "⚠️ Undeclared Geographic Discrepancy: Photo taken in a different city than reported incident"
            if image_analysis.get("image_fraud_reason"):
                image_analysis["image_fraud_reason"] += f" | {discrepancy_msg}"
            else:
                image_analysis["image_fraud_reason"] = discrepancy_msg

    # 12.6 METADATA STRIPPED & VLM GEOGRAPHIC INCONGRUITY PENALTIES
    if exif_gps_status == "METADATA_STRIPPED" and not is_live_capture:
        fraud_score = min(1.0, fraud_score + 0.25)
        stripped_msg = "⚠️ METADATA_STRIPPED: Damage photo lacks authentic camera EXIF GPS metadata"
        if image_analysis.get("image_fraud_reason"):
            image_analysis["image_fraud_reason"] += f" | {stripped_msg}"
        else:
            image_analysis["image_fraud_reason"] = stripped_msg

    vlm_geo_incongruity = bool(vlm_result.get("vlm_geographic_incongruity", False))
    vlm_geo_reason = str(vlm_result.get("vlm_geographic_incongruity_reason", "NONE"))

    if vlm_geo_incongruity:
        fraud_score = min(1.0, fraud_score + 0.35)
        incongruity_msg = f"🚨 GEOGRAPHIC_INCONGRUITY: Non-Indian scene markers detected in photo ({vlm_geo_reason})"
        if image_analysis.get("image_fraud_reason"):
            image_analysis["image_fraud_reason"] += f" | {incongruity_msg}"
        else:
            image_analysis["image_fraud_reason"] = incongruity_msg

    # 13. CONSISTENCY CHECK (MERGES TEXT DESCRIPTION WITH YOLO & GEMINI VLM FINDINGS)
    vlm_visual_desc = vlm_result.get("vlm_damage_description", "")
    combined_visual_findings = list(damage_results["detections"])
    
    if vlm_visual_desc:
        combined_visual_findings.append({"class": vlm_visual_desc, "confidence": 0.90})

    consistency_result = check_claim_consistency(
        description=description,
        detections=combined_visual_findings,
        claim_amount=claim_amount
    )

    # 🔗 SYNERGY ENFORCEMENT: Enforce HIGHLY_INCONSISTENT only on severe fraud, duplicate photo, or model mismatch
    has_severe_inconsistency = (
        any("Mismatch" in m for m in mismatch_flags) or 
        image_analysis.get("is_duplicate", False) or 
        (image_analysis.get("ai_fraud_score", 0.0) > 0.50)
    )
    if has_severe_inconsistency:
        consistency_result["overall_status"] = "HIGHLY_INCONSISTENT"
        consistency_result["consistency_score"] = min(consistency_result.get("consistency_score", 1.0), 0.20)
        
        if "issues" not in consistency_result or not isinstance(consistency_result["issues"], list):
            consistency_result["issues"] = []

        if mismatch_flags:
            consistency_result["issues"].append({
                "type": "vehicle_mismatch",
                "message": f"Vehicle Identity Notice: {mismatch_flags[0]}"
            })
        if image_analysis.get("image_fraud_reason"):
            consistency_result["issues"].append({
                "type": "image_forensics",
                "message": f"Forensic Alert: {image_analysis['image_fraud_reason']}"
            })

    fraud_score = min(
        fraud_score + consistency_result.get("fraud_score_addition", 0.0),
        1.0
    )

    # 14. PATTERN ANALYSIS
    pattern_result = analyze_claim_patterns(
        db=db,
        customer_name=customer_name,
        city=city,
        car_model=car_model,
        user_id=user_id
    )

    fraud_score = min(
        fraud_score + pattern_result["fraud_score_addition"],
        1.0
    )

    # 15. DYNAMIC CONTINUOUS ML COST ESTIMATION
    # Continuous damage severity from YOLO count, confidence, and VLM severity
    yolo_count = len(damage_results.get("detections", []))
    vlm_sev = str(vlm_result.get("vlm_severity", "")).lower()
    vlm_sev_factor = 0.85 if "severe" in vlm_sev else (0.50 if "moderate" in vlm_sev else 0.25)
    continuous_sev = (0.35 * damage_conf) + (0.35 * min(yolo_count, 5) / 5.0) + (0.30 * vlm_sev_factor)
    continuous_sev = round(float(np.clip(continuous_sev, 0.05, 0.95)), 3)

    cost_result = estimate_repair_cost(
        damage_confidence=damage_conf,
        claim_amount=claim_amount,
        driver_fault=driver_fault,
        fraud_score=fraud_score,
        vehicle_make=car_model,
        vehicle_age=vehicle_age,
        vehicle_condition="good",
        damage_severity=continuous_sev,
        detection_count=yolo_count,
        vlm_severity=vlm_sev,
        detections=damage_results.get("detections", [])
    )

    # 16. AI DECISION ENGINE
    decision_result = decide_claim(
        fraud_score=fraud_score,
        fault_type=fault_result["fault"],
        claim_amount=claim_amount
    )

    if vlm_geo_incongruity:
        # Geographic Fraud Rejection: Non-Indian roadway/vehicle markers detected by VLM
        decision_result["ai_decision"] = "reject_suggested"
        decision_result["ai_reason"] = f"Geographic Fraud: Non-Indian roadway/vehicle scene detected by VLM ({vlm_geo_reason})."
    elif is_post_transit_bool:
        # Enforce manual review (bypassing zero-touch STP auto-payout for declared post-transit claims)
        if decision_result.get("ai_decision") == "approve_suggested":
            decision_result["ai_decision"] = "manual_review_suggested"
            decision_result["ai_reason"] = "Declared Post-Transit Inspection — human adjuster sign-off required per protocol."
    elif exif_gps_status == "METADATA_STRIPPED" and not is_live_capture:
        # Revoke STP auto-approval if EXIF metadata is missing/stripped
        if decision_result.get("ai_decision") == "approve_suggested":
            decision_result["ai_decision"] = "manual_review_suggested"
            decision_result["ai_reason"] = "Missing/stripped camera EXIF GPS metadata — manual adjuster verification required."


    # 17. EXPLAINABLE AI & LLM EXECUTIVE SUMMARY
    try:
        consistency_issues_list = json.loads(json.dumps(consistency_result["issues"]))
    except Exception:
        consistency_issues_list = []

    xai_result = generate_explanation(
        fraud_score=fraud_score,
        fault_type=fault_result["fault"],
        consistency_score=consistency_result["consistency_score"],
        consistency_issues=consistency_issues_list,
        exif_fraud_flag=image_analysis["exif_fraud_flag"],
        image_fraud_reason=image_analysis["image_fraud_reason"],
        claim_amount=claim_amount,
        estimated_cost=cost_result["estimated_cost"],
        ela_score=image_analysis["ela_score"],
        damage_severity=damage_results.get("severity", "none"),
        is_live_capture=is_live_capture,
        device_latitude=device_latitude,
        device_longitude=device_longitude,
        capture_timestamp=capture_timestamp,
        walkaround_video_url=walkaround_video_url,
        garage_audit_json=garage_audit_json_str,
        is_post_transit=is_post_transit_bool,
        incident_location=incident_location,
        inspection_location=inspection_location,
        transit_reason=transit_reason,
        geo_discrepancy_detected=geo_discrepancy_detected,
        photo_capture_lat=photo_capture_lat,
        photo_capture_lon=photo_capture_lon,
        submission_device_lat=submission_device_lat,
        submission_device_lon=submission_device_lon,
        exif_gps_status=exif_gps_status,
        geographic_incongruity=vlm_geo_incongruity,
        geographic_incongruity_reason=vlm_geo_reason
    )

    # Generate Gemini LLM Summary for Insurance Agent
    hardware_proof_note = (
        f" [Live Camera & GPS Verified: Lat {device_latitude}, Lng {device_longitude}, Time {capture_timestamp}]"
        if is_live_capture else " [Standard File Upload]"
    )
    llm_summary = generate_claim_summary_llm({
        "customer_name": customer_name,
        "car_model": car_model,
        "claim_amount": claim_amount,
        "fraud_score": round(fraud_score, 2),
        "vlm_damage_description": vlm_result.get("vlm_damage_description", "") + hardware_proof_note,
        "consistency_status": consistency_result["overall_status"],
        "image_fraud_reason": image_analysis.get("image_fraud_reason", "")
    })

    timeline = json.dumps([
        {
            "status": "submitted",
            "timestamp": datetime.now().isoformat(),
            "note": "Claim submitted by customer" + (" (Live Camera Capture)" if is_live_capture else "")
        }
    ])

    # 18. SAVE CLAIM TO DATABASE
    new_claim = Claim(
        customer_name=customer_name,
        car_model=car_model,
        city=city,
        policy_type=policy_type,
        claim_amount=claim_amount,
        description=description,
        damage_detected=damage_info,
        heatmap_image=heatmap_path,
        fault_type=fault_result["fault"],
        fault_confidence=fault_result["confidence"],
        fraud_score=round(fraud_score, 2),
        risk_level=xai_result["risk_level"],
        consistency_score=consistency_result["consistency_score"],
        consistency_status=consistency_result["overall_status"],
        consistency_issues=json.dumps(consistency_result["issues"]),
        ai_decision=decision_result["ai_decision"],
        ai_confidence=decision_result["ai_confidence"],
        ai_reason=decision_result["ai_reason"],
        approved_amount=decision_result["approved_amount"],
        number_plate=plate_info,
        estimated_cost=cost_result["estimated_cost"],
        cost_flag=cost_result["flag"],
        cost_flag_reason=cost_result["flag_reason"],
        images=json.dumps(saved_paths),
        garage_estimate_pdf=garage_pdf_path,
        image_hash=image_analysis["image_hash"],
        ela_score=image_analysis["ela_score"],
        image_fraud_reason=image_analysis["image_fraud_reason"],
        exif_data=str(image_analysis.get("exif_timestamp", "")),
        exif_fraud_flag=image_analysis["exif_fraud_flag"],
        xai_explanation=json.dumps(xai_result["factors"]),
        garage_audit_json=garage_audit_json_str,

        # Hardware Capture & Location Proof
        device_latitude=device_latitude,
        device_longitude=device_longitude,
        capture_timestamp=capture_timestamp,
        is_live_capture=is_live_capture,
        walkaround_video_url=walkaround_video_url,

        # Split Incident & Inspection Declaration
        is_post_transit=is_post_transit_bool,
        incident_location=incident_location,
        inspection_location=inspection_location,
        transit_reason=transit_reason,

        # Decoupled Telemetry & VLM Geographic Incongruity
        photo_capture_lat=photo_capture_lat,
        photo_capture_lon=photo_capture_lon,
        submission_device_lat=submission_device_lat,
        submission_device_lon=submission_device_lon,
        exif_gps_status=exif_gps_status,
        geographic_incongruity=vlm_geo_incongruity,
        geographic_incongruity_reason=vlm_geo_reason,

        # VLM & LLM Fields
        vlm_damage_description=vlm_result.get("vlm_damage_description", ""),
        vlm_severity=vlm_result.get("vlm_severity", ""),
        vlm_is_genuine=final_vlm_is_genuine,
        vlm_number_plate=vlm_result.get("vlm_number_plate", "NOT_VISIBLE"),
        vlm_estimated_cost_min=vlm_result.get("vlm_estimated_cost_min", 0.0),
        vlm_estimated_cost_max=vlm_result.get("vlm_estimated_cost_max", 0.0),
        vlm_claim_summary=llm_summary,

        status_timeline=timeline,
        user_id=user_id,
        status="pending",
        decision="under_review",
        final_decision="pending",
        review_status="awaiting_review"
    )


    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)
    # 7. PROCESS WALKAROUND VIDEO (IF PROVIDED)
    if walkaround_video_url:
        video_analysis = process_walkaround_video(walkaround_video_url, vehicle_number, new_claim.claim_id)
        new_claim.video_analysis_json = json.dumps(video_analysis)
        db.commit()
        db.refresh(new_claim)

    return new_claim


@router.get("/all-claims", response_model=list[ClaimResponse])
def get_all_claims(db: Session = Depends(get_db)):
    return db.query(Claim).all()


@router.get("/my-claims", response_model=list[ClaimResponse])
def get_my_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload:
            user_id = payload.get("user_id")
            return db.query(Claim).filter(Claim.user_id == user_id).all()
    return []


@router.get("/claim/{claim_id}", response_model=ClaimResponse)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.get("/report/{claim_id}")
def download_report(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    pdf_path = generate_claim_pdf(claim)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"claim_{claim_id}_report.pdf")


class AgentReview(BaseModel):
    final_decision: str
    agent_notes: str = ""
    approved_amount: float = 0.0


@router.put("/review/{claim_id}")
def agent_review(claim_id: int, review: AgentReview, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    try:
        timeline = json.loads(claim.status_timeline or "[]")
    except Exception:
        timeline = []

    timeline.append({
        "status": review.final_decision,
        "timestamp": datetime.now().isoformat(),
        "note": f"Agent decision: {review.final_decision}"
    })

    claim.final_decision = review.final_decision
    claim.agent_notes = review.agent_notes
    claim.approved_amount = review.approved_amount
    claim.review_status = "reviewed"
    claim.status = review.final_decision
    claim.status_timeline = json.dumps(timeline)

    db.commit()
    db.refresh(claim)

    return {"message": "Review submitted!", "claim_id": claim_id, "final_decision": review.final_decision}


@router.post("/settle/{claim_id}")
def settle_claim(claim_id: int, request: SettlementRequest, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    try:
        timeline = json.loads(claim.status_timeline or "[]")
    except Exception:
        timeline = []

    status_word = "approved" if request.final_amount >= claim.claim_amount else "counter_offered"
    if request.final_amount == 0:
        status_word = "rejected"

    timeline.append({
        "status": f"settled_{status_word}",
        "timestamp": datetime.now().isoformat(),
        "note": f"Adjuster authorized settlement: ₹{request.final_amount}"
    })

    claim.final_approved_amount = request.final_amount
    claim.settlement_notes = request.notes
    claim.settlement_status = status_word
    claim.review_status = "settled"
    claim.status = f"settled_{status_word}"
    claim.status_timeline = json.dumps(timeline)

    db.commit()
    db.refresh(claim)

    # Re-generate PDF with the addendum
    try:
        generate_claim_pdf(claim)
    except Exception as e:
        print(f"Error regenerating PDF with addendum: {e}")

    return {"message": "Settlement Authorized", "claim_id": claim_id, "settlement_status": status_word}

@router.get("/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    claims = db.query(Claim).all()
    
    total_claims_count = len(claims)
    total_claimed_value = sum(c.claim_amount for c in claims if c.claim_amount)
    
    total_settled_value = 0
    total_fraud_loss_prevented = 0
    
    stp_count = 0
    
    # Fraud vectors
    duplicate_dhash = 0
    stock_or_ai_forgery = 0
    directional_contradiction = 0
    inflated_garage_estimate = 0
    
    # Status distribution
    status_distribution = {
        "approved": 0,
        "settled_adjusted": 0,
        "manual_review": 0,
        "rejected": 0,
        "pending": 0
    }
    
    make_wise_dict = {}

    for c in claims:
        # Settlement Value
        settled_val = c.final_approved_amount if c.final_approved_amount is not None else (c.approved_amount if c.approved_amount is not None else 0)
        total_settled_value += settled_val
        
        # Fraud Loss Prevented
        if c.review_status in ["settled", "reviewed", "rejected"]:
            prevented = (c.claim_amount or 0) - settled_val
            if prevented > 0 and (c.fraud_score > 0.4 or c.exif_fraud_flag or (c.garage_audit_json and "INFLATED" in c.garage_audit_json)):
                total_fraud_loss_prevented += prevented
                
        # STP
        if c.ai_decision == "approved" and c.risk_level == "LOW":
            stp_count += 1
            
        # Fraud Vectors
        reason = str(c.image_fraud_reason or "").lower()
        if "dhash" in reason or "duplicate" in reason:
            duplicate_dhash += 1
        
        if c.vlm_is_genuine is False or c.exif_fraud_flag or (c.ela_score and c.ela_score > 0.7):
            stock_or_ai_forgery += 1
            
        if c.consistency_status == "CONTRADICTION":
            directional_contradiction += 1
            
        if c.garage_audit_json and "INFLATED" in c.garage_audit_json:
            inflated_garage_estimate += 1
            
        # Status
        if c.review_status == "awaiting_review":
            status_distribution["manual_review"] += 1
        elif c.review_status == "settled" or c.review_status == "reviewed":
            stat = getattr(c, "settlement_status", None) or c.final_decision
            if stat == "approved":
                status_distribution["approved"] += 1
            elif stat == "rejected":
                status_distribution["rejected"] += 1
            else:
                status_distribution["settled_adjusted"] += 1
        else:
            status_distribution["pending"] += 1
            
        # Make Wise
        make = c.car_model.split(" ")[0].upper() if c.car_model else "UNKNOWN"
        if make not in make_wise_dict:
            make_wise_dict[make] = {"total_claims": 0, "sum_amount": 0}
        make_wise_dict[make]["total_claims"] += 1
        make_wise_dict[make]["sum_amount"] += (c.claim_amount or 0)

    make_wise_stats = [
        {
            "make": make,
            "total_claims": data["total_claims"],
            "avg_claim_amount": data["sum_amount"] / data["total_claims"]
        }
        for make, data in make_wise_dict.items()
    ]
    
    return {
        "total_claims_count": total_claims_count,
        "total_claimed_value": total_claimed_value,
        "total_settled_value": total_settled_value,
        "total_fraud_loss_prevented": total_fraud_loss_prevented,
        "stp_rate": (stp_count / total_claims_count * 100) if total_claims_count > 0 else 0,
        "avg_turnaround_time_seconds": 22.4,
        "fraud_vector_breakdown": {
            "duplicate_dhash": duplicate_dhash,
            "stock_or_ai_forgery": stock_or_ai_forgery,
            "directional_contradiction": directional_contradiction,
            "inflated_garage_estimate": inflated_garage_estimate
        },
        "status_distribution": status_distribution,
        "make_wise_stats": sorted(make_wise_stats, key=lambda x: x["total_claims"], reverse=True)
    }

@router.get("/{claim_id}/download-pdf")
def download_claim_pdf(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    file_path = generate_claim_pdf(claim)
    return FileResponse(file_path, media_type="application/pdf", filename=f"claim_{claim_id}_inspection_report.pdf")