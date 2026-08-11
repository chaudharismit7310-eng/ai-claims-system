def decide_claim(fraud_score: float, fault_type: str, claim_amount: float) -> dict:

    # High fraud - straight reject
    if fraud_score > 0.75:
        return {
            "ai_decision": "reject_suggested",
            "ai_confidence": round(fraud_score, 2),
            "ai_reason": "High fraud probability detected by AI",
            "approved_amount": 0.0
        }

    if fault_type == "driver_fault":
        if fraud_score > 0.5:
            return {
                "ai_decision": "reject_suggested",
                "ai_confidence": round(fraud_score, 2),
                "ai_reason": "Driver at fault with suspicious fraud activity",
                "approved_amount": 0.0
            }
        else:
            return {
                "ai_decision": "partial_suggested",
                "ai_confidence": 0.70,
                "ai_reason": "Driver at fault - AI suggests 50% partial coverage",
                "approved_amount": round(claim_amount * 0.5, 2)
            }

    elif fault_type == "opponent_fault":
        return {
            "ai_decision": "approve_suggested",
            "ai_confidence": 0.90,
            "ai_reason": "Opponent at fault - AI suggests full coverage",
            "approved_amount": round(claim_amount * 0.9, 2)
        }

    elif fault_type == "natural":
        return {
            "ai_decision": "approve_suggested",
            "ai_confidence": 0.88,
            "ai_reason": "Natural cause detected - AI suggests full coverage",
            "approved_amount": round(claim_amount * 0.95, 2)
        }

    else:  # unclear
        return {
            "ai_decision": "manual_review_suggested",
            "ai_confidence": 0.50,
            "ai_reason": "Fault unclear - human agent review required",
            "approved_amount": 0.0
        }