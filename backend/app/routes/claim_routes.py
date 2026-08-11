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
from app.schemas.claim_schema import ClaimResponse

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
from app.services.vlm_service import analyze_damage_with_vlm, generate_claim_summary_llm

from app.utils.pdf_generator import generate_claim_pdf
from app.auth import decode_token

import shutil
import os
import json
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

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

    # 3. SAVE GARAGE ESTIMATE PDF (IF PROVIDED)
    garage_pdf_path = ""
    if garage_pdf and garage_pdf.filename:
        os.makedirs("uploads/garage", exist_ok=True)
        garage_pdf_path = f"uploads/garage/{garage_pdf.filename}"
        with open(garage_pdf_path, "wb") as pdf_buffer:
            shutil.copyfileobj(garage_pdf.file, pdf_buffer)

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

    # 11. BASE FRAUD SCORE CALCULATION & INTERNET DOWNLOAD OVERRIDE
    is_internet_download = (
        image_analysis.get("exif_fraud_flag", False) or 
        "stock" in image_analysis.get("image_fraud_reason", "").lower() or 
        "duplicate" in image_analysis.get("image_fraud_reason", "").lower()
    )
    final_vlm_is_genuine = bool(vlm_result.get("vlm_is_genuine", True) and not is_internet_download)

    fraud_result = detect_fraud(
        damage_confidence=damage_conf,
        driver_fault=driver_fault,
        natural_cause=natural_cause,
        claim_amount=claim_amount
    )

    fraud_score = min(
        fraud_result["fraud_score"] + image_analysis["fraud_score_addition"],
        1.0
    )

    if not final_vlm_is_genuine:
        fraud_score = min(fraud_score + 0.20, 1.0)

    # 12. CAR MODEL & VEHICLE IDENTITY CROSS-VALIDATION
    mismatch_flags = []

    if user_id:
        user_vehicles = db.query(VehicleModel).filter(VehicleModel.user_id == user_id).all()
        user_vehicle = None

        if vehicle_number:
            for v in user_vehicles:
                v_num = (getattr(v, "vehicle_number", None) or getattr(v, "license_plate", None) or "").replace(" ", "").upper()
                if v_num and v_num == vehicle_number.replace(" ", "").upper():
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
            reg_plate = registered_plate_str.replace(" ", "").upper()
            photo_plate = str(plate_info).replace(" ", "").upper()

            if reg_plate and photo_plate not in ["NOT_DETECTED", "NOT_VISIBLE", ""]:
                if reg_plate != photo_plate and reg_plate not in photo_plate:
                    mismatch_flags.append(f"Plate Mismatch: Registered '{registered_plate_str}' vs Photo Detected '{plate_info}'")

    if mismatch_flags:
        has_real_mismatch = any("Mismatch" in m for m in mismatch_flags)
        fraud_score = min(fraud_score + (0.35 if has_real_mismatch else 0.10), 1.0)
        
        mismatch_msg = " | ".join(mismatch_flags)

        if image_analysis.get("image_fraud_reason"):
            image_analysis["image_fraud_reason"] += f" | 🚨 {mismatch_msg}"
        else:
            image_analysis["image_fraud_reason"] = f"🚨 {mismatch_msg}"

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

    # 🔗 SYNERGY ENFORCEMENT: If Vehicle Mismatch, Duplicate Image, Stock Photo, or Forgery exists, force HIGHLY_INCONSISTENT
    if mismatch_flags or image_analysis.get("image_fraud_reason") or not final_vlm_is_genuine:
        consistency_result["overall_status"] = "HIGHLY_INCONSISTENT"
        consistency_result["consistency_score"] = min(consistency_result.get("consistency_score", 1.0), 0.15)
        
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

    # 15. COST ESTIMATION
    cost_result = estimate_repair_cost(
        damage_confidence=damage_conf,
        claim_amount=claim_amount,
        driver_fault=driver_fault,
        fraud_score=fraud_score
    )

    # 16. AI DECISION ENGINE
    decision_result = decide_claim(
        fraud_score=fraud_score,
        fault_type=fault_result["fault"],
        claim_amount=claim_amount
    )

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
        damage_severity=damage_results.get("severity", "none")
    )

    # Generate Gemini LLM Summary for Insurance Agent
    llm_summary = generate_claim_summary_llm({
        "customer_name": customer_name,
        "car_model": car_model,
        "claim_amount": claim_amount,
        "fraud_score": round(fraud_score, 2),
        "vlm_damage_description": vlm_result.get("vlm_damage_description", ""),
        "consistency_status": consistency_result["overall_status"],
        "image_fraud_reason": image_analysis.get("image_fraud_reason", "")
    })

    timeline = json.dumps([
        {
            "status": "submitted",
            "timestamp": datetime.now().isoformat(),
            "note": "Claim submitted by customer"
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