from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    vehicle_number = Column(String, unique=True)
    car_model = Column(String)
    policy_number = Column(String)
    policy_expiry_date = Column(String)
    rc_document = Column(String, default="")
    policy_document = Column(String, default="")
    status = Column(String, default="pending_verification")
    agent_notes = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())