import cv2
import numpy as np
import os
import json

def generate_damage_heatmap(image_path: str, detections: list) -> str:
    """
    Generate damage heatmap on car image
    Red = severe, Yellow = moderate, Green = minor
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return image_path

        height, width = img.shape[:2]
        
        # Create heatmap overlay
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        for detection in detections:
            if "bbox" in detection:
                bbox = detection["bbox"]
                confidence = detection.get("confidence", 0.5)
                
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                
                # Clamp to image bounds
                x1 = max(0, min(x1, width-1))
                y1 = max(0, min(y1, height-1))
                x2 = max(0, min(x2, width-1))
                y2 = max(0, min(y2, height-1))
                
                # Add heat based on confidence
                heatmap[y1:y2, x1:x2] += confidence

        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        # Convert to color heatmap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )

        # Blend with original image
        result = cv2.addWeighted(img, 0.6, heatmap_colored, 0.4, 0)

        # Draw bounding boxes
        for detection in detections:
            if "bbox" in detection:
                bbox = detection["bbox"]
                confidence = detection.get("confidence", 0.5)
                class_name = detection.get("class", "damage")

                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                x1 = max(0, min(x1, width-1))
                y1 = max(0, min(y1, height-1))
                x2 = max(0, min(x2, width-1))
                y2 = max(0, min(y2, height-1))

                # Color based on severity
                if confidence > 0.7:
                    color = (0, 0, 255)    # Red - severe
                elif confidence > 0.4:
                    color = (0, 165, 255)  # Orange - moderate
                else:
                    color = (0, 255, 0)    # Green - minor

                cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

                label = f"{class_name}: {confidence:.0%}"
                cv2.putText(result, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Add severity legend
        legend_items = [
            ("Severe", (0, 0, 255)),
            ("Moderate", (0, 165, 255)),
            ("Minor", (0, 255, 0))
        ]
        for i, (label, color) in enumerate(legend_items):
            y_pos = 20 + i * 25
            cv2.rectangle(result, (10, y_pos-12), (30, y_pos+5), color, -1)
            cv2.putText(result, label, (35, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        # Save heatmap
        os.makedirs("uploads/heatmaps", exist_ok=True)
        filename = os.path.basename(image_path)
        heatmap_path = f"uploads/heatmaps/heatmap_{filename}"
        cv2.imwrite(heatmap_path, result)

        return heatmap_path

    except Exception as e:
        print(f"Heatmap generation error: {e}")
        return image_path