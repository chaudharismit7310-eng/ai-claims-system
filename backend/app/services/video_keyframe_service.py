import os
import cv2
from typing import Dict, Any
from app.services.ocr_service import extract_number_plate
from app.ai_models.yolov8_model import detect_damage

def process_walkaround_video(video_path: str, registered_plate: str, claim_id: int) -> Dict[str, Any]:
    """
    Extracts 4 keyframes from a video at 15%, 40%, 65%, and 90% duration marks.
    Runs Plate Extraction and Damage Detection on each keyframe.
    """
    if not os.path.exists(video_path):
        return {
            "keyframes": [],
            "plate_verified_in_video": False,
            "damage_verified_in_video": False,
            "video_duration_seconds": 0.0,
            "verification_confidence": 0.0,
            "summary": "Video file not found."
        }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "keyframes": [],
            "plate_verified_in_video": False,
            "damage_verified_in_video": False,
            "video_duration_seconds": 0.0,
            "verification_confidence": 0.0,
            "summary": "Failed to open video file."
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps if fps > 0 else 0.0

    target_percentages = [0.15, 0.40, 0.65, 0.90]
    keyframes_paths = []
    
    os.makedirs("uploads/keyframes", exist_ok=True)
    
    plate_verified = False
    damage_verified = False

    for i, pct in enumerate(target_percentages):
        target_frame_idx = int(total_frames * pct)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
        ret, frame = cap.read()
        if ret:
            frame_path = f"uploads/keyframes/claim_{claim_id}_frame_{i+1}.jpg"
            cv2.imwrite(frame_path, frame)
            keyframes_paths.append(frame_path)

            # Analyze frame
            ocr_res = extract_number_plate(frame_path)
            plate_text = ocr_res.get("plate_text", "")
            
            # Simple substring/equivalence check (stripping spaces)
            safe_reg_plate = registered_plate.replace(" ", "").lower() if registered_plate else ""
            safe_ocr_plate = plate_text.replace(" ", "").lower() if plate_text else ""
            
            if safe_reg_plate and safe_reg_plate in safe_ocr_plate:
                plate_verified = True

            damage_res = detect_damage(frame_path)
            if damage_res.get("severity", "none") != "none":
                damage_verified = True

    cap.release()

    confidence = 0.0
    if plate_verified and damage_verified:
        confidence = 0.95
        summary = "Both license plate and damage verified across 360° walkaround video."
    elif plate_verified:
        confidence = 0.60
        summary = "License plate verified in video, but no explicit damage detected in keyframes."
    elif damage_verified:
        confidence = 0.50
        summary = "Damage detected in video, but license plate could not be verified."
    else:
        confidence = 0.20
        summary = "Neither damage nor plate could be verified in the extracted keyframes."

    return {
        "keyframes": keyframes_paths,
        "plate_verified_in_video": plate_verified,
        "damage_verified_in_video": damage_verified,
        "video_duration_seconds": round(duration_seconds, 2),
        "verification_confidence": confidence,
        "summary": summary
    }
