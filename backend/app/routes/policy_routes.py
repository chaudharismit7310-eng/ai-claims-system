from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.policy_model import Policy

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.post("/add-policy")
def add_policy(
    user_id: int,
    policy_number: str,
    vehicle_number: str,
    car_model: str,
    policy_type: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    new_policy = Policy(
        user_id=user_id,
        policy_number=policy_number,
        vehicle_number=vehicle_number,
        car_model=car_model,
        policy_type=policy_type,
        start_date=start_date,
        end_date=end_date,
        status="active"
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy

@router.get("/verify/{policy_number}")
def verify_policy(policy_number: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.policy_number == policy_number).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found ❌")
    if policy.status != "active":
        raise HTTPException(status_code=400, detail="Policy expired ❌")
    return {"valid": True, "policy": policy}