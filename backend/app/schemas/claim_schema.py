from pydantic import BaseModel
from typing import Optional, List


class ClaimBase(BaseModel):
    customer_name: str
    car_model: str
    city: str
    policy_type: str
    claim_amount: float
    description: str


class ClaimCreate(ClaimBase):
    pass


class SettlementRequest(BaseModel):
    final_amount: float
    notes: str


class ClaimResponse(ClaimBase):
    claim_id: int
    damage_detected: Optional[str] = None
    heatmap_image: Optional[str] = None
    fault_type: Optional[str] = None
    fault_confidence: Optional[float] = None
    fraud_score: Optional[float] = None
    risk_level: Optional[str] = None
    consistency_score: Optional[float] = None
    consistency_status: Optional[str] = None
    consistency_issues: Optional[str] = None
    ai_decision: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reason: Optional[str] = None
    approved_amount: Optional[float] = None
    number_plate: Optional[str] = None
    estimated_cost: Optional[float] = None
    cost_flag: Optional[str] = None
    cost_flag_reason: Optional[str] = None
    images: Optional[str] = None
    garage_estimate_pdf: Optional[str] = None
    image_hash: Optional[str] = None
    ela_score: Optional[float] = None
    image_fraud_reason: Optional[str] = None
    exif_data: Optional[str] = None
    exif_fraud_flag: Optional[bool] = None
    xai_explanation: Optional[str] = None

    # 🤖 NEW VLM & LLM FIELDS (Required for FastAPI Serialization)
    vlm_damage_description: Optional[str] = None
    vlm_severity: Optional[str] = None
    vlm_is_genuine: Optional[bool] = True
    vlm_number_plate: Optional[str] = None
    vlm_estimated_cost_min: Optional[float] = 0.0
    vlm_estimated_cost_max: Optional[float] = 0.0
    vlm_claim_summary: Optional[str] = None

    status_timeline: Optional[str] = None
    status: Optional[str] = None
    decision: Optional[str] = None
    final_decision: Optional[str] = None
    review_status: Optional[str] = None

    # Hardware Capture & Location Proof
    device_latitude: Optional[float] = None
    device_longitude: Optional[float] = None
    capture_timestamp: Optional[str] = None
    is_live_capture: Optional[bool] = False
    walkaround_video_url: Optional[str] = None
    video_analysis_json: Optional[str] = None
    garage_audit_json: Optional[str] = None

    # Settlement Addendum
    final_approved_amount: Optional[float] = None
    settlement_notes: Optional[str] = None
    settlement_status: Optional[str] = None

    # Split Incident & Inspection Declaration
    is_post_transit: Optional[bool] = False
    incident_location: Optional[str] = None
    inspection_location: Optional[str] = None
    transit_reason: Optional[str] = None

    # Decoupled Telemetry & VLM Geographic Incongruity
    photo_capture_lat: Optional[float] = None
    photo_capture_lon: Optional[float] = None
    submission_device_lat: Optional[float] = None
    submission_device_lon: Optional[float] = None
    exif_gps_status: Optional[str] = "METADATA_STRIPPED"
    geographic_incongruity: Optional[bool] = False
    geographic_incongruity_reason: Optional[str] = None


    class Config:
        from_attributes = True