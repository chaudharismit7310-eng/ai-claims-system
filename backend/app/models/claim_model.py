from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    car_model = Column(String)
    city = Column(String)
    policy_type = Column(String)
    claim_amount = Column(Float)
    description = Column(String)
    status = Column(String, default="pending")
    fraud_score = Column(Float, default=0.0)
    decision = Column(String, default="under_review")
    damage_detected = Column(String, default="")
    fault_type = Column(String, default="unclear")
    fault_confidence = Column(Float, default=0.0)
    ai_decision = Column(String, default="pending")
    ai_confidence = Column(Float, default=0.0)
    ai_reason = Column(String, default="")
    approved_amount = Column(Float, default=0.0)
    final_decision = Column(String, default="pending")
    review_status = Column(String, default="awaiting_review")
    agent_notes = Column(String, default="")
    number_plate = Column(String, default="")
    estimated_cost = Column(Float, default=0.0)
    cost_flag = Column(String, default="")
    cost_flag_reason = Column(String, default="")
    images = Column(Text, default="")
    garage_estimate_pdf = Column(String, default="")
    exif_data = Column(Text, default="")
    exif_fraud_flag = Column(Boolean, default=False)
    status_timeline = Column(Text, default="")
    vehicle_id = Column(Integer, default=None)
    user_id = Column(Integer, default=None)
    image_hash = Column(String, default="")
    ela_score = Column(Float, default=0.0)
    image_fraud_reason = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
    heatmap_image = Column(String, default="")
    consistency_score = Column(Float, default=1.0)
    consistency_status = Column(String, default="")
    consistency_issues = Column(Text, default="")
    xai_explanation = Column(Text, default="")
    risk_level = Column(String, default="LOW")
    
    # VLM & LLM Multimodal Fields
    vlm_damage_description = Column(Text, default="")
    vlm_severity = Column(String, default="")
    vlm_is_genuine = Column(Boolean, default=True)
    vlm_number_plate = Column(String, default="")
    vlm_estimated_cost_min = Column(Float, default=0.0)
    vlm_estimated_cost_max = Column(Float, default=0.0)
    vlm_claim_summary = Column(Text, default="")

    # Hardware Capture & Location Proof
    device_latitude = Column(Float, nullable=True)
    device_longitude = Column(Float, nullable=True)
    capture_timestamp = Column(String, nullable=True)
    is_live_capture = Column(Boolean, default=False)
    walkaround_video_url = Column(String, nullable=True)
    video_analysis_json = Column(String, nullable=True)
    garage_audit_json = Column(String, nullable=True)
    
    # Settlement Addendum
    final_approved_amount = Column(Float, nullable=True)
    settlement_notes = Column(Text, nullable=True)
    settlement_status = Column(String, default="pending")

    # Split Incident & Inspection Declaration (Post-Transit Triage Engine)
    is_post_transit = Column(Boolean, default=False)
    incident_location = Column(String, nullable=True)
    inspection_location = Column(String, nullable=True)
    transit_reason = Column(String, nullable=True)

    # Decoupled Telemetry (Camera EXIF vs Client Browser GPS) & VLM Scene Incongruity
    photo_capture_lat = Column(Float, nullable=True)
    photo_capture_lon = Column(Float, nullable=True)
    submission_device_lat = Column(Float, nullable=True)
    submission_device_lon = Column(Float, nullable=True)
    exif_gps_status = Column(String, default="METADATA_STRIPPED")
    geographic_incongruity = Column(Boolean, default=False)
    geographic_incongruity_reason = Column(String, default="")
