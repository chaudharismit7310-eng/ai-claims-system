import os
from typing import Dict, Any
from app.ai_models.yolov8_model import detect_damage as yolo_detect_damage

def detect_damage(image_path: str) -> Dict[str, Any]:
    """
    Genuine vehicle damage detection service.
    Delegates directly to custom trained YOLOv8 model (car_damage_model.pt).
    Returns real bounding boxes, detected classes, and confidence scores.
    """
    if not os.path.exists(image_path):
        return {
            "error": f"Image file not found at path: {image_path}",
            "damage_detected": False,
            "damage_severity": 0.0,
            "damage_confidence": 0.0,
            "detections_count": 0,
            "detections": []
        }

    try:
        yolo_result = yolo_detect_damage(image_path)
        detections = yolo_result.get("detections", [])
        max_conf = float(yolo_result.get("max_confidence", 0.0))

        # Format detection entries uniformly
        formatted_detections = []
        for d in detections:
            formatted_detections.append({
                "label": d.get("class", "damage"),
                "confidence": d.get("confidence", 0.0),
                "bbox": d.get("bbox", [])
            })

        count = len(formatted_detections)
        # Continuous damage severity based on detections count and max confidence
        if count > 0:
            severity = min(1.0, (count * 0.18) + (max_conf * 0.50))
        else:
            severity = 0.0

        return {
            "damage_detected": count > 0,
            "damage_severity": round(severity, 3),
            "damage_confidence": round(max_conf, 3),
            "detections_count": count,
            "detections": formatted_detections,
            "severity_level": yolo_result.get("severity", "none")
        }

    except Exception as e:
        print(f"Damage detection service error: {e}")
        return {
            "error": str(e),
            "damage_detected": False,
            "damage_severity": 0.0,
            "damage_confidence": 0.0,
            "detections_count": 0,
            "detections": []
        }