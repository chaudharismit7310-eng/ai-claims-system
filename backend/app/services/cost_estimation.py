import os
import numpy as np
from datetime import datetime
from app.ai_models.cost_model import estimate_repair_cost as objective_cost_estimator

# India specific car value mapping (INR)
INDIA_CAR_VALUES = {
    'maruti':    600000,   'suzuki':   600000,
    'hyundai':   800000,   'honda':    900000,
    'tata':      700000,   'mahindra': 900000,
    'toyota':    1200000,  'kia':      1000000,
    'ford':      900000,   'volkswagen': 1100000,
    'renault':   700000,   'nissan':   800000,
    'bmw':       4000000,  'mercedes': 5000000,
    'audi':      3500000,  'default':  800000
}

def estimate_repair_cost(
    damage_confidence: float = 0.5,
    claim_amount: float = 0.0,
    driver_fault: bool = False,
    fraud_score: float = 0.0,
    vehicle_make: str = "default",
    vehicle_age: int = 4,
    vehicle_condition: str = "good",
    **kwargs
) -> dict:
    """
    Enforces objective, vision-driven actuarial cost modeling.
    Completely excludes claimed_amount from valuation calculation.
    Uses physical damage inputs (YOLOv8 classes, bboxes, panel count, VLM severity),
    vehicle market base value, and vehicle age.
    """
    make_lower = vehicle_make.lower() if vehicle_make else "default"

    # Identify brand from string
    detected_brand = "default"
    for brand in INDIA_CAR_VALUES:
        if brand != "default" and brand in make_lower:
            detected_brand = brand
            break

    base_car_value = float(INDIA_CAR_VALUES.get(detected_brand, INDIA_CAR_VALUES['default']))
    current_year = datetime.now().year
    vehicle_year = current_year - max(0, int(vehicle_age))

    vehicle_details = {
        "price": base_car_value,
        "year": vehicle_year,
        "make": vehicle_make
    }

    # Extract damage detections and severity
    damage_detections = kwargs.get("detections", [])
    if not damage_detections:
        det_count = int(kwargs.get("detection_count", 1))
        damage_detections = [{"class": "damage", "confidence": float(damage_confidence)}] * max(1, det_count)

    vlm_sev_str = str(kwargs.get("vlm_severity", "")).lower()
    if not vlm_sev_str or vlm_sev_str == "none":
        damage_severity_arg = kwargs.get("damage_severity")
        if damage_severity_arg is not None:
            sev_val = float(damage_severity_arg)
            vlm_sev_str = "severe" if sev_val > 0.65 else ("moderate" if sev_val > 0.35 else "minor")
        else:
            vlm_sev_str = "moderate"

    # Compute objective valuation strictly independent of claimed_amount
    actuarial_res = objective_cost_estimator(
        vehicle_details=vehicle_details,
        damage_detections=damage_detections,
        vlm_severity=vlm_sev_str
    )

    estimated = actuarial_res["predicted_cost"]
    cost_range_min = actuarial_res["cost_range_min"]
    cost_range_max = actuarial_res["cost_range_max"]

    # Continuous depreciation based on vehicle age
    car_value_inr = max(150000.0, float(base_car_value * (0.92 ** min(max(int(vehicle_age), 0), 15))))

    # Overcharge audit check comparing customer claim vs AI objective estimate
    difference = round(claim_amount - estimated, 2)
    overcharge_pct = round((difference / claim_amount) * 100, 1) if claim_amount > 0 else 0

    if overcharge_pct > 40:
        flag = "Overcharged"
        flag_reason = (f"Claimed Rs.{claim_amount:,.2f} but AI estimates "
                       f"Rs.{estimated:,.2f} — {overcharge_pct}% higher")
    elif overcharge_pct < -10:
        flag = "Undercharged"
        flag_reason = "Claimed amount is lower than estimated repair cost"
    else:
        flag = "Fair"
        flag_reason = "Claimed amount matches estimated repair cost"

    damage_sev_val = kwargs.get("damage_severity", damage_confidence)
    try:
        damage_sev_float = round(float(damage_sev_val), 3)
    except (ValueError, TypeError):
        damage_sev_float = round(float(damage_confidence), 3)

    return {
        "estimated_cost": estimated,
        "predicted_cost": estimated,
        "cost_range_min": cost_range_min,
        "cost_range_max": cost_range_max,
        "claimed_amount": claim_amount,
        "difference": difference,
        "overcharge_percent": overcharge_pct,
        "damage_severity": damage_sev_float,
        "car_valuation": round(car_value_inr, 2),
        "flag": flag,
        "flag_reason": flag_reason,
        "model_version": "vision_actuarial_objective_v3"
    }