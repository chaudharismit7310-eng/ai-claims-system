from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from app.models.claim_model import Claim
from app.models.vehicle_model import Vehicle
from app.auth import decode_token

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer(auto_error=False)


def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token missing!")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token!")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required!")
    return payload


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    total_users = db.query(User).count()
    total_claims = db.query(Claim).count()
    total_vehicles = db.query(Vehicle).count()
    pending_vehicles = db.query(Vehicle).filter(
        Vehicle.status == "pending_verification"
    ).count()
    pending_claims = db.query(Claim).filter(
        Claim.review_status == "awaiting_review"
    ).count()
    approved_claims = db.query(Claim).filter(
        Claim.final_decision == "approved"
    ).count()
    rejected_claims = db.query(Claim).filter(
        Claim.final_decision == "rejected"
    ).count()

    return {
        "total_users": total_users,
        "total_claims": total_claims,
        "total_vehicles": total_vehicles,
        "pending_vehicles": pending_vehicles,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
    }


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]


@router.get("/vehicles")
def get_all_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    return db.query(Vehicle).all()


@router.get("/claims")
def get_all_claims(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    return db.query(Claim).all()


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    if role not in ["customer", "agent", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role!")
    user.role = role
    db.commit()
    return {"message": f"User role updated to {role}!"}