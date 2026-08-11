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
    print(f"✅ Real Cost Model loaded! R²={model_data['r2_score']:.4f}")
except Exception as e:
    print(f"⚠️ Cost model not loaded: {e}")
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

    # Car value — India specific
    make_lower = vehicle_make.lower() if vehicle_make else "default"
    car_value_inr = INDIA_CAR_VALUES.get(make_lower, INDIA_CAR_VALUES['default'])

    # Condition mapping
    condition_map = {
        'new': 5, 'like new': 4, 'excellent': 3,
        'good': 2, 'fair': 1, 'salvage': 0
    }
    condition_num = condition_map.get(vehicle_condition.lower(), 2)

    # Damage severity from confidence
    if damage_confidence > 0.7:
        damage_severity = 0.85  # Severe
    elif damage_confidence > 0.4:
        damage_severity = 0.60  # Moderate
    else:
        damage_severity = 0.30  # Minor

    if cost_model is not None:
        features = np.array([[
            vehicle_age,       # vehicle_age
            condition_num,     # condition_num
            0,                 # make_encoded (default)
            0,                 # type_encoded (default)
            car_value_inr,     # car_value_inr
            damage_severity,   # damage_severity
            50000              # odometer (default)
        ]])

        estimated = float(cost_model.predict(features)[0])
        estimated = max(1000, round(estimated, 2))

    else:
        # Fallback formula
        base = car_value_inr * damage_severity * 0.3
        estimated = max(1000, round(base, 2))

    # Overcharge check
    difference    = round(claim_amount - estimated, 2)
    overcharge_pct = round((difference / claim_amount) * 100, 1) if claim_amount > 0 else 0

    if overcharge_pct > 40:
        flag        = "Overcharged"
        flag_reason = (f"Claimed Rs.{claim_amount} but AI estimates "
                      f"Rs.{estimated} — {overcharge_pct}% higher")
    elif overcharge_pct < -10:
        flag        = "Undercharged"
        flag_reason = "Claimed amount is lower than estimated repair cost"
    else:
        flag        = "Fair"
        flag_reason = "Claimed amount matches estimated repair cost"

    return {
        "estimated_cost":    estimated,
        "claimed_amount":    claim_amount,
        "difference":        difference,
        "overcharge_percent": overcharge_pct,
        "flag":              flag,
        "flag_reason":       flag_reason,
        "model_version":     "real_kaggle_v2_r2_0.94"
    }