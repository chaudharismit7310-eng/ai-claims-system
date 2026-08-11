import os
import pickle
import numpy as np

# Path to our trained Kaggle + Vision Random Forest Model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ai_models", "fraud_model.pkl")

# Load trained weights on startup
try:
    with open(MODEL_PATH, "rb") as f:
        fraud_model = pickle.load(f)
    print("✅ Real Kaggle-Trained Fraud Detection Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Warning: Could not load fraud model from {MODEL_PATH}. Error: {e}")
    fraud_model = None

def detect_fraud(
    damage_confidence: float = 0.8,
    driver_fault: bool = False,
    natural_cause: bool = False,
    claim_amount: float = 50000.0,
    previous_claims: int = 0,
    **kwargs
) -> dict:
    """
    Evaluates claim fraud probability using the real trained Random Forest model.
    Accepts direct parameter calls as well as flexible claim dictionary kwargs.
    """
    total_claim_amount = float(claim_amount)

    # Calculate financial breakdown estimates for model features
    injury_claim = total_claim_amount * 0.15
    property_claim = total_claim_amount * 0.25
    vehicle_claim = total_claim_amount * 0.60

    # Extract additional kwargs with sensible defaults matching model schema
    months_as_customer = kwargs.get("months_as_customer", 24)
    policy_deductable = kwargs.get("policy_deductable", 1000)
    umbrella_limit = kwargs.get("umbrella_limit", 0)
    bodily_injuries = kwargs.get("bodily_injuries", 1 if driver_fault else 0)
    
    # Vision & Image Forensics Scores
    vision_damage_severity = float(damage_confidence)
    image_forgery_score = kwargs.get("image_forgery_score", 0.1 if not natural_cause else 0.05)

    if fraud_model is not None:
        # Construct feature array matching the 10 trained features in exact order:
        # [months_as_customer, policy_deductable, umbrella_limit, total_claim_amount, 
        #  injury_claim, property_claim, vehicle_claim, bodily_injuries, 
        #  vision_damage_severity, image_forgery_score]
        feature_vector = np.array([[
            months_as_customer,
            policy_deductable,
            umbrella_limit,
            total_claim_amount,
            injury_claim,
            property_claim,
            vehicle_claim,
            bodily_injuries,
            vision_damage_severity,
            image_forgery_score
        ]])

        # Predict probability of fraud (Class 1)
        fraud_prob = float(fraud_model.predict_proba(feature_vector)[0][1])
    else:
        # Fallback calculation if model file is missing
        fraud_prob = 0.25

    # Determine Risk Category
    if fraud_prob >= 0.70:
        risk_level = "CRITICAL"
    elif fraud_prob >= 0.50:
        risk_level = "HIGH"
    elif fraud_prob >= 0.30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "fraud_score": round(fraud_prob, 2),
        "risk_level": risk_level,
        "is_suspicious": fraud_prob > 0.50
    }

# Backward Compatibility Alias
calculate_fraud_score = detect_fraud