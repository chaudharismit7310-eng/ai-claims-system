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

    class Config:
        from_attributes = True