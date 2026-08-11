from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_model import User
from app.auth import hash_password, verify_password, create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "customer"

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered!")
    new_user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role=data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered!", "user_id": new_user.id, "role": new_user.role}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password!")
    token = create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "name": user.name}