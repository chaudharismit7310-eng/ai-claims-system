from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    policy_number = Column(String, unique=True, index=True)
    vehicle_number = Column(String)
    car_model = Column(String)
    policy_type = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    status = Column(String, default="active")