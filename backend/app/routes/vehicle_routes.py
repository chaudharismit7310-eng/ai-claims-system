from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.vehicle_model import Vehicle
from app.models.user_model import User  # ✅ Added
from app.auth import decode_token
from app.services.email_service import send_vehicle_status  # ✅ Added
import shutil
import os

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
security = HTTPBearer(auto_error=False)

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token missing!")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token!")
    return payload


@router.post("/add")
async def add_vehicle(
    vehicle_number: str = Form(...),
    car_model: str = Form(...),
    policy_number: str = Form(...),
    policy_expiry_date: str = Form(...),
    rc_document: UploadFile = File(...),
    policy_document: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    existing = db.query(Vehicle).filter(
        Vehicle.vehicle_number == vehicle_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle already registered!")

    rc_path = f"{UPLOAD_DIR}/rc_{vehicle_number}_{rc_document.filename}"
    with open(rc_path, "wb") as f:
        shutil.copyfileobj(rc_document.file, f)

    policy_path = f"{UPLOAD_DIR}/policy_{vehicle_number}_{policy_document.filename}"
    with open(policy_path, "wb") as f:
        shutil.copyfileobj(policy_document.file, f)

    new_vehicle = Vehicle(
        user_id=current_user["user_id"],
        vehicle_number=vehicle_number,
        car_model=car_model,
        policy_number=policy_number,
        policy_expiry_date=policy_expiry_date,
        rc_document=rc_path,
        policy_document=policy_path,
        status="pending_verification"
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return {
        "message": "Vehicle added!",
        "vehicle_id": new_vehicle.vehicle_id,
        "status": "pending_verification"
    }


@router.get("/my-vehicles")
def get_my_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(Vehicle).filter(
        Vehicle.user_id == current_user["user_id"]
    ).all()


@router.get("/verified")
def get_verified_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from datetime import datetime
    vehicles = db.query(Vehicle).filter(
        Vehicle.user_id == current_user["user_id"],
        Vehicle.status == "verified"
    ).all()
    
    # Filter out expired policies
    active_vehicles = []
    for v in vehicles:
        try:
            expiry = datetime.strptime(v.policy_expiry_date, "%Y-%m-%d")
            if expiry >= datetime.now():
                active_vehicles.append(v)
        except:
            active_vehicles.append(v)
    
    return active_vehicles


@router.get("/pending")
def get_pending_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied!")

    return db.query(Vehicle).filter(
        Vehicle.status.in_(["pending_verification", "under_review"])
    ).all()


@router.get("/all")
def get_all_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied!")

    return db.query(Vehicle).all()


@router.put("/verify/{vehicle_id}")
async def verify_vehicle(
    vehicle_id: int,
    action: str = Form(...),
    agent_notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied!")

    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found!")

    vehicle.status = action
    vehicle.agent_notes = agent_notes

    db.commit()
    db.refresh(vehicle)

    # ✅ Send email notification
    try:
        user = db.query(User).filter(
            User.id == vehicle.user_id
        ).first()

        if user and user.email:
            send_vehicle_status(
                user.email,
                vehicle.vehicle_number,
                action,
                agent_notes
            )
    except:
        pass

    return {
        "message": f"Vehicle {action}!",
        "vehicle_id": vehicle_id,
        "status": action
    }