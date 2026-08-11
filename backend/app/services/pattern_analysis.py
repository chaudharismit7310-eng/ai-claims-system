from sqlalchemy.orm import Session
from app.models.claim_model import Claim

def analyze_claim_patterns(
    db: Session,
    customer_name: str,
    city: str,
    car_model: str,
    user_id: int = None
) -> dict:
    """
    Detect suspicious claim patterns
    """
    patterns = []
    fraud_addition = 0.0

    # Pattern 1: Same customer multiple claims
    customer_claims = db.query(Claim).filter(
        Claim.customer_name == customer_name
    ).all()

    if len(customer_claims) >= 3:
        patterns.append({
            "type": "FREQUENT_CLAIMANT",
            "message": f"Customer has {len(customer_claims)} previous claims",
            "severity": "HIGH" if len(customer_claims) >= 5 else "MEDIUM"
        })
        fraud_addition += 0.15 if len(customer_claims) >= 5 else 0.08

    # Pattern 2: Same city frequent claims
    city_claims = db.query(Claim).filter(
        Claim.city == city
    ).count()

    if city_claims >= 10:
        patterns.append({
            "type": "HIGH_RISK_LOCATION",
            "message": f"Location '{city}' has {city_claims} claims — high risk area",
            "severity": "MEDIUM"
        })
        fraud_addition += 0.05

    # Pattern 3: Same car model frequent claims
    car_claims = db.query(Claim).filter(
        Claim.car_model == car_model,
        Claim.customer_name == customer_name
    ).count()

    if car_claims >= 2:
        patterns.append({
            "type": "REPEAT_VEHICLE_CLAIM",
            "message": f"Same vehicle '{car_model}' claimed {car_claims} times",
            "severity": "HIGH"
        })
        fraud_addition += 0.20

    # Pattern 4: Recent claim from same user
    if user_id:
        recent_claims = db.query(Claim).filter(
            Claim.user_id == user_id,
            Claim.status.in_(["approved", "pending"])
        ).count()

        if recent_claims >= 2:
            patterns.append({
                "type": "MULTIPLE_ACTIVE_CLAIMS",
                "message": f"User has {recent_claims} active/approved claims",
                "severity": "MEDIUM"
            })
            fraud_addition += 0.10

    return {
        "patterns_found": len(patterns),
        "patterns": patterns,
        "fraud_score_addition": round(min(fraud_addition, 0.4), 2),
        "is_suspicious": len(patterns) > 0,
        "pattern_summary": " | ".join([p["message"] for p in patterns])
    }