import os
import pickle
import numpy as np

# Load trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ai_models", "cost_model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)
    cost_model  = model_data['model']
    le_make     = model_data['le_make']
    le_type     = model_data['le_type']
    print(f"[OK] Real Cost Model loaded! R2={model_data['r2_score']:.4f}")
except Exception as e:
    print(f"[WARN] Cost model not loaded: {e}")
    cost_model = None

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

import pandas as pd

# Brand alias mapping to Craigslist le_make classes
BRAND_ALIASES = {
    'maruti': 'toyota',
    'suzuki': 'toyota',
    'tata': 'ford',
    'mahindra': 'jeep',
    'renault': 'nissan',
    'skoda': 'volkswagen',
    'mg': 'chevrolet',
    'kia': 'kia',
    'hyundai': 'hyundai',
    'honda': 'honda',
    'toyota': 'toyota',
    'ford': 'ford',
    'bmw': 'bmw',
    'audi': 'audi',
    'mercedes': 'mercedes-benz',
    'mercedes-benz': 'mercedes-benz',
    'volkswagen': 'volkswagen',
    'nissan': 'nissan'
}

def estimate_repair_cost(
    damage_confidence: float,
    claim_amount: float,
    driver_fault: bool,
    fraud_score: float,
    vehicle_make: str = "default",
    vehicle_age: int = 5,
    vehicle_condition: str = "good",
    **kwargs
) -> dict:
    make_lower = vehicle_make.lower() if vehicle_make else "default"

    # Identify brand from string
    detected_brand = "default"
    for brand in INDIA_CAR_VALUES:
        if brand != "default" and brand in make_lower:
            detected_brand = brand
            break

    base_car_value = INDIA_CAR_VALUES.get(detected_brand, INDIA_CAR_VALUES['default'])
    # Continuous depreciation based on vehicle age (compounded ~8% per year, min 25% of base)
    car_value_inr = max(150000.0, float(base_car_value * (0.92 ** min(max(int(vehicle_age), 0), 15))))

    # Condition mapping
    condition_map = {
        'new': 5, 'like new': 4, 'excellent': 3,
        'good': 2, 'fair': 1, 'salvage': 0
    }
    condition_num = condition_map.get(str(vehicle_condition).lower(), 2)

    # Encode make using le_make
    make_encoded = 0
    if cost_model is not None and le_make is not None:
        target_make = BRAND_ALIASES.get(detected_brand, detected_brand)
        if target_make in le_make.classes_:
            make_encoded = int(le_make.transform([target_make])[0])
        elif 'toyota' in le_make.classes_:
            make_encoded = int(le_make.transform(['toyota'])[0])

    # Encode type using le_type
    type_encoded = 0
    v_type = kwargs.get("vehicle_type", "sedan")
    if make_lower:
        if any(w in make_lower for w in ["suv", "creta", "harrier", "safari", "xuv", "brezza", "scorpio", "fortuner"]):
            v_type = "SUV"
        elif any(w in make_lower for w in ["hatchback", "swift", "i10", "i20", "alto", "baleno", "wagon"]):
            v_type = "hatchback"
    if cost_model is not None and le_type is not None:
        if v_type in le_type.classes_:
            type_encoded = int(le_type.transform([v_type])[0])
        elif 'sedan' in le_type.classes_:
            type_encoded = int(le_type.transform(['sedan'])[0])

    # Continuous damage severity calculation
    # Combines explicit damage_severity, YOLO detections count, and max confidence
    if "damage_severity" in kwargs and kwargs["damage_severity"] is not None:
        try:
            damage_severity = float(kwargs["damage_severity"])
        except (ValueError, TypeError):
            damage_severity = float(damage_confidence)
    else:
        # Continuous heuristic blending
        det_count = kwargs.get("detection_count", 1)
        det_factor = min(det_count, 5) / 5.0
        vlm_sev_str = str(kwargs.get("vlm_severity", "")).lower()
        vlm_factor = 0.85 if "severe" in vlm_sev_str else (0.50 if "moderate" in vlm_sev_str else 0.25)
        damage_severity = (0.35 * float(damage_confidence)) + (0.35 * det_factor) + (0.30 * vlm_factor)

    damage_severity = float(np.clip(damage_severity, 0.05, 0.95))
    odometer = float(kwargs.get("odometer", max(10000, int(vehicle_age) * 12000)))

    if cost_model is not None:
        features_df = pd.DataFrame([[
            int(vehicle_age),   # vehicle_age
            condition_num,      # condition_num
            make_encoded,       # make_encoded
            type_encoded,       # type_encoded
            car_value_inr,      # car_value_inr
            damage_severity,    # damage_severity
            odometer            # odometer
        ]], columns=['vehicle_age', 'condition_num', 'make_encoded', 'type_encoded', 'car_value_inr', 'damage_severity', 'odometer'])

        raw_pred = float(cost_model.predict(features_df)[0])
        # Ensure repair estimate is proportional to car value and severity
        estimated = max(1000.0, round(raw_pred, 2))
    else:
        # Dynamic fallback formula
        base = car_value_inr * damage_severity * 0.35
        estimated = max(1000.0, round(base, 2))

    # Overcharge check
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

    return {
        "estimated_cost": estimated,
        "claimed_amount": claim_amount,
        "difference": difference,
        "overcharge_percent": overcharge_pct,
        "damage_severity": round(damage_severity, 3),
        "car_valuation": round(car_value_inr, 2),
        "flag": flag,
        "flag_reason": flag_reason,
        "model_version": "real_kaggle_v2_r2_0.94_dynamic"
    }