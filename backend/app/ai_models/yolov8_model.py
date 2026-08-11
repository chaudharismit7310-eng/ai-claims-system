from ultralytics import YOLO
import os

model = None

def load_model():
    global model
    
    paths = [
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

def detect_damage(image_path: str) -> dict:
    global model
    if model is None:
        load_model()

    results = model(image_path, conf=0.25)

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
        if max_conf > 0.7:
            severity = "severe"
        elif max_conf > 0.4:
            severity = "moderate"
        else:
            severity = "minor"

    damage_types = list(set(d["class"] for d in detections))

    return {
        "image_path": image_path,
        "detections": detections,
        "total_objects": len(detections),
        "severity": severity,
        "damage_types": damage_types,
        "max_confidence": round(max_conf, 3)
    }