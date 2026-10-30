import re
from app.utils.plate_normalizer import normalize_plate

def check_claim_consistency(
    description: str = "",
    detections: list = None,
    claim_amount: float = 0.0,
    claim_data: dict = None,
    ocr_text: str = ""
) -> dict:
    """
    Comprehensive Claim Consistency Checker:
    1. License Plate & Car Model Cross-Validation (OCR / Submitted Data)
    2. Directional Text vs. Vision Cross-Validation (e.g., Rear impact vs. Front damage)
    3. Damage Severity, Amount Mismatch, Vague Description & Multiple Area Checks
    """
    if detections is None:
        detections = []
    if claim_data is None:
        claim_data = {}

    description_lower = (description or "").lower()
    issues = []
    consistency_score = 1.0

    # -------------------------------------------------------------
    # SECTION 1: License Plate & Car Model Mismatch Checks
    # -------------------------------------------------------------
    raw_submitted_plate = str(claim_data.get("license_plate", "") or claim_data.get("vehicle_number", ""))
    submitted_plate = normalize_plate(raw_submitted_plate)
    cleaned_ocr = normalize_plate(ocr_text)

    # Check 1A: License Plate Mismatch
    if submitted_plate and cleaned_ocr and cleaned_ocr not in ["NOTDETECTED", "NOTVISIBLE"]:
        if submitted_plate != cleaned_ocr and submitted_plate not in cleaned_ocr and cleaned_ocr not in submitted_plate:
            issues.append({
                "type": "LICENSE_PLATE_MISMATCH",
                "message": f"License Plate Mismatch: Claim submitted '{raw_submitted_plate or submitted_plate}', but OCR detected '{ocr_text or cleaned_ocr}'",
                "severity": "CRITICAL"
            })
            consistency_score -= 0.35

    # Check 1B: Car Model / Brand Mismatch
    submitted_car_model = str(claim_data.get("car_model", "")).lower()
    known_brands = ["honda", "toyota", "hyundai", "maruti", "suzuki", "bmw", "mercedes", "audi", "ford", "tata", "mahindra", "ertiga", "swift", "city", "creta"]
    submitted_brand = next((b for b in known_brands if b in submitted_car_model), None)

    if submitted_brand and cleaned_ocr:
        detected_other_brands = [b for b in known_brands if b in cleaned_ocr.lower() and b != submitted_brand]
        if detected_other_brands:
            issues.append({
                "type": "CAR_MODEL_MISMATCH",
                "message": f"Car Model Mismatch: Claim specifies '{submitted_car_model.title()}', but image suggests '{detected_other_brands[0].title()}'",
                "severity": "CRITICAL"
            })
            consistency_score -= 0.35

    # -------------------------------------------------------------
    # SECTION 2: Directional Text vs. Vision Cross-Validation
    # -------------------------------------------------------------
    text_mentions_front = any(k in description_lower for k in ["front", "bonnet", "hood", "grille", "headlight", "windshield", "front bumper"])
    text_mentions_rear = any(k in description_lower for k in ["rear", "back", "dicky", "trunk", "taillight", "back bumper", "behind"])
    text_mentions_side = any(k in description_lower for k in ["side", "door", "fender", "mirror", "left side", "right side"])

    # Extract visual features from detections
    visual_detected_classes = [
        d.get("class", "").lower() if isinstance(d, dict) else str(d).lower()
        for d in detections
    ]
    visual_detected_str = " ".join(visual_detected_classes).lower()

    visual_has_front = any(k in visual_detected_str for k in ["front", "bumper", "bonnet", "grille", "headlight", "hood", "windshield"])
    visual_has_rear = any(k in visual_detected_str for k in ["rear", "back", "taillight", "trunk", "dicky"])
    visual_has_side = any(k in visual_detected_str for k in ["door", "fender", "side", "mirror"])

    # Directional Contradiction Checks
    if text_mentions_rear and not text_mentions_front and visual_has_front and not visual_has_rear:
        issues.append({
            "type": "DIRECTIONAL_DISCREPANCY",
            "message": "Directional Mismatch: Description reports REAR impact, but uploaded photo shows FRONT-END damage!",
            "severity": "CRITICAL"
        })
        consistency_score -= 0.40

    if text_mentions_front and not text_mentions_rear and visual_has_rear and not visual_has_front:
        issues.append({
            "type": "DIRECTIONAL_DISCREPANCY",
            "message": "Directional Mismatch: Description reports FRONT impact, but uploaded photo shows REAR damage!",
            "severity": "CRITICAL"
        })
        consistency_score -= 0.40

    if text_mentions_side and not (text_mentions_front or text_mentions_rear) and not visual_has_side and (visual_has_front or visual_has_rear):
        issues.append({
            "type": "DIRECTIONAL_DISCREPANCY",
            "message": "Directional Mismatch: Description reports SIDE impact, but photo shows no side damage.",
            "severity": "HIGH"
        })
        consistency_score -= 0.30

    # -------------------------------------------------------------
    # SECTION 3: Damage Severity, Amount & Description Checks
    # -------------------------------------------------------------
    body_parts = {
        "front": ["front", "bumper", "hood", "headlight", "grille"],
        "rear": ["rear", "back", "trunk", "tail", "behind"],
        "side": ["side", "door", "fender", "mirror", "window"],
        "roof": ["roof", "top", "ceiling"],
        "wheel": ["wheel", "tyre", "tire", "rim"],
        "glass": ["glass", "windshield", "windscreen", "window"]
    }

    damage_types = {
        "dent": ["dent", "dented", "bent", "deformed"],
        "scratch": ["scratch", "scratched", "scraped", "scuff"],
        "crack": ["crack", "cracked", "broken", "shattered"],
        "total": ["total loss", "completely damaged", "write off", "totaled"]
    }

    max_confidence = max([d.get("confidence", 0) for d in detections if isinstance(d, dict)], default=0.5)

    # Check 3A: Severity Mismatch
    mentioned_total = any(kw in description_lower for kw in damage_types["total"])
    if mentioned_total and max_confidence < 0.5:
        issues.append({
            "type": "SEVERITY_MISMATCH",
            "message": "Description mentions total loss, but visual damage confidence is low",
            "severity": "HIGH"
        })
        consistency_score -= 0.30

    # Check 3B: Amount vs. Damage Severity
    if claim_amount > 100000 and max_confidence < 0.3:
        issues.append({
            "type": "AMOUNT_DAMAGE_MISMATCH",
            "message": f"High claim amount (₹{claim_amount:,.0f}) submitted, but low damage confidence detected",
            "severity": "HIGH"
        })
        consistency_score -= 0.25

    # Check 3C: No Damage Detected
    if len(detections) == 0:
        issues.append({
            "type": "NO_DAMAGE_DETECTED",
            "message": "No visible damage detected in uploaded images",
            "severity": "CRITICAL"
        })
        consistency_score -= 0.40

    # Check 3D: Vague Description
    if description_lower and len(description_lower.split()) < 5:
        issues.append({
            "type": "VAGUE_DESCRIPTION",
            "message": "Incident description is too short and vague",
            "severity": "LOW"
        })
        consistency_score -= 0.10

    # Check 3E: Multiple Damage Areas vs. Detected Count
    mentioned_parts = [part for part, keywords in body_parts.items() if any(kw in description_lower for kw in keywords)]
    if len(mentioned_parts) > 2 and len(detections) <= 1:
        issues.append({
            "type": "MULTIPLE_AREA_MISMATCH",
            "message": f"Description mentions {len(mentioned_parts)} damage areas, but only {len(detections)} detected in image",
            "severity": "MEDIUM"
        })
        consistency_score -= 0.15

    # -------------------------------------------------------------
    # SECTION 4: Overall Rating & Score Normalization
    # -------------------------------------------------------------
    consistency_score = max(0.0, round(consistency_score, 2))

    if consistency_score >= 0.8:
        overall = "CONSISTENT"
    elif consistency_score >= 0.6:
        overall = "MINOR_INCONSISTENCY"
    elif consistency_score >= 0.4:
        overall = "MAJOR_INCONSISTENCY"
    else:
        overall = "HIGHLY_INCONSISTENT"

    fraud_score_addition = round((1.0 - consistency_score) * 0.40, 2)

    return {
        "consistency_score": consistency_score,
        "overall_status": overall,
        "issues": issues,
        "issues_count": len(issues),
        "is_consistent": len(issues) == 0,
        "fraud_score_addition": fraud_score_addition
    }

# Backward Compatibility Alias
check_consistency = check_claim_consistency