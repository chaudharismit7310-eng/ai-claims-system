import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

X_train = np.array([
    [0.2, 8000,  0, 0.1, 1],
    [0.3, 12000, 0, 0.1, 1],
    [0.3, 15000, 0, 0.1, 1],
    [0.4, 18000, 0, 0.1, 1],
    [0.4, 20000, 1, 0.2, 1],
    [0.5, 25000, 0, 0.1, 1],
    [0.5, 30000, 0, 0.2, 2],
    [0.6, 35000, 0, 0.2, 2],
    [0.6, 40000, 0, 0.2, 2],
    [0.6, 45000, 1, 0.3, 2],
    [0.7, 50000, 0, 0.2, 2],
    [0.7, 55000, 0, 0.2, 2],
    [0.7, 60000, 0, 0.2, 3],
    [0.8, 65000, 0, 0.2, 3],
    [0.8, 70000, 0, 0.2, 3],
    [0.8, 75000, 0, 0.3, 3],
    [0.9, 80000, 0, 0.2, 3],
    [0.9, 90000, 0, 0.3, 3],
    [0.9, 100000,0, 0.2, 3],
    [0.95,120000, 0, 0.3, 3],
    [0.3, 90000, 1, 0.8, 1],
    [0.2, 80000, 1, 0.9, 1],
    [0.4, 70000, 1, 0.7, 1],
    [0.3, 60000, 1, 0.8, 1],
    [0.7, 48000, 0, 0.1, 2],
    [0.8, 75000, 0, 0.1, 3],
    [0.6, 38000, 0, 0.1, 2],
    [0.5, 28000, 0, 0.1, 2],
])

y_train = np.array([
    7000,  10000, 13000, 16000, 14000,
    22000, 26000, 31000, 36000, 33000,
    45000, 50000, 54000, 59000, 63000,
    68000, 74000, 82000, 90000, 108000,
    12000, 10000, 15000, 13000,
    44000, 70000, 35000, 25000,
])

cost_model = GradientBoostingRegressor(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    random_state=42
)
cost_model.fit(X_train, y_train)

def estimate_repair_cost(
    damage_confidence: float,
    claim_amount: float,
    driver_fault: bool,
    fraud_score: float
) -> dict:

    if damage_confidence > 0.7:
        severity = 3
    elif damage_confidence > 0.5:
        severity = 2
    else:
        severity = 1

    features = np.array([[
        damage_confidence,
        claim_amount,
        1 if driver_fault else 0,
        fraud_score,
        severity
    ]])

    estimated = cost_model.predict(features)[0]
    estimated = max(0, round(float(estimated), 2))

    difference = round(claim_amount - estimated, 2)
    overcharge_pct = round(
        (difference / claim_amount) * 100, 1
    ) if claim_amount > 0 else 0

    if overcharge_pct > 40:
        flag = "Overcharged"
        flag_reason = (
            f"Claimed Rs.{claim_amount} but AI estimates "
            f"Rs.{estimated} — {overcharge_pct}% higher"
        )
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
        "flag": flag,
        "flag_reason": flag_reason
    }