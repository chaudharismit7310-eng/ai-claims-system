def generate_explanation(
    fraud_score: float,
    fault_type: str,
    consistency_score: float,
    consistency_issues: list,
    exif_fraud_flag: bool,
    image_fraud_reason: str,
    claim_amount: float,
    estimated_cost: float,
    ela_score: float,
    damage_severity: str
) -> dict:
    """
    Generate explainable AI breakdown of fraud risk
    """
    factors = []
    total_contribution = 0.0

    # Factor 1: Image Duplicate/Forgery
    if "DUPLICATE" in image_fraud_reason:
        factors.append({
            "factor": "Duplicate Image Detected",
            "contribution": 0.40,
            "severity": "CRITICAL",
            "icon": "🔴",
            "detail": "Same image was used in a previous claim"
        })
        total_contribution += 0.40

    # Factor 2: AI Forgery Detection
    if "AI DETECTED" in image_fraud_reason:
        factors.append({
            "factor": "AI Forgery Detection",
            "contribution": 0.35,
            "severity": "HIGH",
            "icon": "🔴",
            "detail": "AI detected image may be from internet or manipulated"
        })
        total_contribution += 0.35

    # Factor 3: ELA Score
    if ela_score < 0.01:
        factors.append({
            "factor": "Low ELA Score",
            "contribution": 0.30,
            "severity": "HIGH",
            "icon": "🟠",
            "detail": f"ELA score {ela_score} suggests downloaded/stock image"
        })
        total_contribution += 0.30
    elif ela_score > 0.15:
        factors.append({
            "factor": "High ELA Score",
            "contribution": 0.25,
            "severity": "HIGH",
            "icon": "🟠",
            "detail": f"ELA score {ela_score} suggests heavily edited image"
        })
        total_contribution += 0.25

    # Factor 4: EXIF Issues
    if exif_fraud_flag:
        factors.append({
            "factor": "Missing/Invalid EXIF Data",
            "contribution": 0.15,
            "severity": "MEDIUM",
            "icon": "🟡",
            "detail": "Image metadata missing or suspicious timestamp"
        })
        total_contribution += 0.15

    # Factor 5: Driver Fault
    if fault_type == "driver_fault":
        factors.append({
            "factor": "Driver at Fault",
            "contribution": 0.15,
            "severity": "MEDIUM",
            "icon": "🟡",
            "detail": "Customer admitted fault in description"
        })
        total_contribution += 0.15

    # Factor 6: Claim Consistency
    if consistency_score < 0.6:
        factors.append({
            "factor": "Inconsistent Description",
            "contribution": round((1 - consistency_score) * 0.3, 2),
            "severity": "HIGH",
            "icon": "🟠",
            "detail": f"Description doesn't match image damage (score: {consistency_score})"
        })
        total_contribution += round((1 - consistency_score) * 0.3, 2)

    # Factor 7: Overcharged
    if claim_amount > 0 and estimated_cost > 0:
        overcharge = (claim_amount - estimated_cost) / claim_amount
        if overcharge > 0.4:
            factors.append({
                "factor": "Overcharged Claim",
                "contribution": 0.12,
                "severity": "MEDIUM",
                "icon": "🟡",
                "detail": f"Claimed ₹{claim_amount:,.0f} but AI estimates ₹{estimated_cost:,.0f} ({overcharge:.0%} higher)"
            })
            total_contribution += 0.12

    # Sort by contribution
    factors.sort(key=lambda x: x["contribution"], reverse=True)

    # Risk level
    if fraud_score >= 0.75:
        risk_level = "CRITICAL"
        risk_color = "red"
        risk_message = "High probability of fraudulent claim"
    elif fraud_score >= 0.5:
        risk_level = "HIGH"
        risk_color = "orange"
        risk_message = "Multiple suspicious indicators detected"
    elif fraud_score >= 0.3:
        risk_level = "MEDIUM"
        risk_color = "yellow"
        risk_message = "Some suspicious indicators — review carefully"
    else:
        risk_level = "LOW"
        risk_color = "green"
        risk_message = "Claim appears genuine"

    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_message": risk_message,
        "fraud_score": round(fraud_score, 2),
        "factors": factors,
        "total_factors": len(factors),
        "top_reason": factors[0]["factor"] if factors else "No suspicious activity"
    }