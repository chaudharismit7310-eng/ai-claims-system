from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import os

model = None

def load_model():
    global model

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))

    paths = [
        os.path.join(project_root, "models", "car_damage_model.pt"),
        "models/car_damage_model.pt",
        "../models/car_damage_model.pt",
        "C:/Users/Dell/ai-claims-system/models/car_damage_model.pt"
    ]

    for custom_path in paths:
        if os.path.exists(custom_path):
            model = YOLO(custom_path)
            print(f"✅ Custom model loaded: {custom_path}")
            print(f"Classes: {list(model.names.values())}")
            return model

    print("⚠️ Generic model loaded")
    model = YOLO("yolov8n.pt")
    return model

def detect_damage(
    image_path: str,
    conf: float = 0.20,
    imgsz: int = 1024,
    iou: float = 0.45
) -> dict:
    global model
    if model is None:
        load_model()

    # Safely load/decode image into memory to support .jfif and avoid FileNotFoundError
    image_input = None
    if isinstance(image_path, str):
        if os.path.exists(image_path):
            image_input = cv2.imread(image_path)
            if image_input is None:
                try:
                    pil_img = Image.open(image_path).convert("RGB")
                    image_input = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    print(f"PIL decode failed for {image_path}: {e}")
        else:
            image_input = image_path
    elif isinstance(image_path, (np.ndarray, Image.Image)):
        image_input = image_path
    else:
        image_input = image_path

    if image_input is None:
        image_input = image_path

    # High-resolution evaluation (imgsz=1024), calibrated conf (0.20), adjusted IoU (0.45)
    # Use augment=True for enhanced multi-damage detection with standard fallback
    try:
        results = model(image_input, imgsz=imgsz, conf=conf, iou=iou, augment=True)
        if not results or len(results[0].boxes) == 0:
            results = model(image_input, imgsz=imgsz, conf=conf, iou=iou)
    except Exception:
        results = model(image_input, imgsz=imgsz, conf=conf, iou=iou)

    detections = []
    for result in results:
        for box in result.boxes:
            class_name = result.names[int(box.cls)]
            confidence = float(box.conf)

            if class_name in ["truck", "car", "bus", "motorcycle", "vehicle"]:
                class_name = "vehicle_damage"

            detections.append({
                "class": class_name,
                "confidence": round(confidence, 3),
                "bbox": box.xyxy[0].tolist()
            })

    if not detections:
        severity = "none"
        max_conf = 0.0
    else:
        max_conf = max(d["confidence"] for d in detections)
        if max_conf > 0.7 or len(detections) >= 3:
            severity = "severe"
        elif max_conf > 0.4 or len(detections) >= 2:
            severity = "moderate"
        else:
            severity = "minor"

    damage_types = list(set(d["class"] for d in detections))

    return {
        "image_path": image_path if isinstance(image_path, str) else "in_memory_image",
        "detections": detections,
        "total_objects": len(detections),
        "severity": severity,
        "damage_types": damage_types,
        "max_confidence": round(max_conf, 3)
    }