from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.claim_model import Claim

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


# =========================================
# SUMMARY ANALYTICS
# =========================================

@router.get("/summary")
def get_summary(

    db: Session = Depends(get_db)

):

    claims = db.query(Claim).all()

    total = len(claims)

    # =====================================
    # DECISION COUNTS
    # =====================================

    approved = len([

        c for c in claims

        if c.final_decision == "approved"

    ])

    rejected = len([

        c for c in claims

        if c.final_decision == "rejected"

    ])

    partial = len([

        c for c in claims

        if c.final_decision == "partial"

    ])

    pending = len([

        c for c in claims

        if c.review_status == "awaiting_review"

    ])

    # =====================================
    # FRAUD SCORE
    # =====================================

    avg_fraud = (

        round(

            sum(c.fraud_score for c in claims)
            / total,

            2
        )

        if total

        else 0
    )

    # =====================================
    # CLAIM AMOUNTS
    # =====================================

    total_claimed = sum(

        c.claim_amount

        for c in claims
    )

    total_approved = sum(

        c.approved_amount

        for c in claims
    )

    # =====================================
    # FAULT TYPE BREAKDOWN
    # =====================================

    fault_types = {}

    for c in claims:

        fault_types[c.fault_type] = (

            fault_types.get(
                c.fault_type,
                0
            ) + 1
        )

    # =====================================
    # AI DECISION BREAKDOWN
    # =====================================

    ai_decisions = {}

    for c in claims:

        ai_decisions[c.ai_decision] = (

            ai_decisions.get(
                c.ai_decision,
                0
            ) + 1
        )

    # =====================================
    # RESPONSE
    # =====================================

    return {

        "total_claims": total,

        "approved": approved,

        "rejected": rejected,

        "partial": partial,

        "pending_review": pending,

        "avg_fraud_score": avg_fraud,

        "total_claimed_amount": total_claimed,

        "total_approved_amount": total_approved,

        "fault_type_breakdown": fault_types,

        "ai_decision_breakdown": ai_decisions
    }


# =========================================
# CLAIM PATTERN ANALYTICS
# =========================================

@router.get("/patterns")
def get_claim_patterns(

    db: Session = Depends(get_db)

):

    claims = db.query(Claim).all()

    # =====================================
    # FREQUENCY TRACKERS
    # =====================================

    customer_freq = {}

    city_freq = {}

    car_freq = {}

    # =====================================
    # COUNT PATTERNS
    # =====================================

    for c in claims:

        # Customer frequency
        customer_freq[c.customer_name] = (

            customer_freq.get(
                c.customer_name,
                0
            ) + 1
        )

        # City frequency
        city_freq[c.city] = (

            city_freq.get(
                c.city,
                0
            ) + 1
        )

        # Car model frequency
        car_freq[c.car_model] = (

            car_freq.get(
                c.car_model,
                0
            ) + 1
        )

    # =====================================
    # SUSPICIOUS CUSTOMERS
    # 3 OR MORE CLAIMS
    # =====================================

    suspicious_customers = {

        k: v

        for k, v in customer_freq.items()

        if v >= 3
    }

    # =====================================
    # HIGH RISK CITIES
    # 5 OR MORE CLAIMS
    # =====================================

    high_risk_cities = {

        k: v

        for k, v in city_freq.items()

        if v >= 5
    }

    # =====================================
    # RESPONSE
    # =====================================

    return {

        "customer_frequency": customer_freq,

        "city_frequency": city_freq,

        "car_frequency": car_freq,

        "suspicious_customers": suspicious_customers,

        "high_risk_cities": high_risk_cities,

        "total_patterns_detected": (

            len(suspicious_customers)

            +

            len(high_risk_cities)
        )
    }