import cv2
import numpy as np
import os
import json
from PIL import Image

def generate_damage_heatmap(image_path: str, detections: list) -> str:
    """
    Generate damage heatmap on car image using 2D Gaussian density accumulation
    and threshold masking to avoid blue tint / washout on undamaged regions.
    Red = severe, Orange = moderate, Green = minor
    """
    try:
        # Read image safely, supporting .jfif and in-memory formats
        img = None
        if isinstance(image_path, str) and os.path.exists(image_path):
            img = cv2.imread(image_path)
            if img is None:
                try:
                    pil_img = Image.open(image_path).convert("RGB")
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    print(f"Failed to read image via PIL in heatmap generator: {e}")
        elif isinstance(image_path, np.ndarray):
            img = image_path.copy()

        if img is None:
            return image_path

        height, width = img.shape[:2]

        # Initialize density_map with float zeros across (h, w)
        density_map = np.zeros((height, width), dtype=np.float32)

        # Accumulate 2D Gaussian kernels for all detected bounding boxes scaled by confidence
        for detection in detections:
            bbox = detection.get("bbox")
            if not bbox or len(bbox) < 4:
                continue
            confidence = float(detection.get("confidence", 0.5))

            x1 = max(0, min(int(bbox[0]), width))
            y1 = max(0, min(int(bbox[1]), height))
            x2 = max(0, min(int(bbox[2]), width))
            y2 = max(0, min(int(bbox[3]), height))

            bw = x2 - x1
            bh = y2 - y1
            if bw <= 0 or bh <= 0:
                continue

            # 2D Gaussian kernel scaled by confidence
            gk_x = cv2.getGaussianKernel(bw, max(bw / 4.0, 1.0))
            gk_y = cv2.getGaussianKernel(bh, max(bh / 4.0, 1.0))
            kernel_2d = (gk_y @ gk_x.T).astype(np.float32)
            if kernel_2d.max() > 0:
                kernel_2d = kernel_2d / kernel_2d.max()

            density_map[y1:y2, x1:x2] += kernel_2d * confidence

        # Normalize accumulated density to [0, 255] (density_norm)
        if density_map.max() > 0:
            density_norm = ((density_map / density_map.max()) * 255.0).astype(np.uint8)
        else:
            density_norm = np.zeros((height, width), dtype=np.uint8)

        # Apply cv2.COLORMAP_JET to density_norm
        heatmap_color = cv2.applyColorMap(density_norm, cv2.COLORMAP_JET)

        # CRITICAL FIX: Generate binary/float threshold mask to eliminate blue washout on undamaged regions
        mask = (density_norm > 15).astype(np.float32)
        # Soften mask boundary slightly for a smooth, natural transition
        mask_blurred = cv2.GaussianBlur(mask, (11, 11), 0)
        mask_3ch = np.repeat(mask_blurred[:, :, np.newaxis], 3, axis=2)

        # Blend heatmap (0.45) with original image (0.55) exclusively over damage regions
        heatmap_blended = cv2.addWeighted(heatmap_color, 0.45, img, 0.55, 0)
        result = (heatmap_blended.astype(np.float32) * mask_3ch + img.astype(np.float32) * (1.0 - mask_3ch)).astype(np.uint8)

        # Draw bounding boxes and severity labels
        for detection in detections:
            bbox = detection.get("bbox")
            if not bbox or len(bbox) < 4:
                continue
            confidence = float(detection.get("confidence", 0.5))
            class_name = detection.get("class") or detection.get("label", "damage")

            x1 = max(0, min(int(bbox[0]), width - 1))
            y1 = max(0, min(int(bbox[1]), height - 1))
            x2 = max(0, min(int(bbox[2]), width - 1))
            y2 = max(0, min(int(bbox[3]), height - 1))

            # Color based on severity
            if confidence > 0.7:
                color = (0, 0, 255)    # Red - severe
            elif confidence > 0.4:
                color = (0, 165, 255)  # Orange - moderate
            else:
                color = (0, 255, 0)    # Green - minor

            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            label = f"{class_name}: {confidence:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            text_y = max(y1 - 8, th + 4)
            # Subtle background box behind label text for high legibility
            cv2.rectangle(result, (x1, text_y - th - 3), (x1 + tw + 4, text_y + 3), (0, 0, 0), -1)
            cv2.putText(result, label, (x1 + 2, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Add severity legend with semi-transparent background
        legend_items = [
            ("Severe", (0, 0, 255)),
            ("Moderate", (0, 165, 255)),
            ("Minor", (0, 255, 0))
        ]
        overlay = result.copy()
        cv2.rectangle(overlay, (5, 5), (120, 85), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.65, result, 0.35, 0, result)

        for i, (label, color) in enumerate(legend_items):
            y_pos = 25 + i * 22
            cv2.rectangle(result, (12, y_pos - 10), (28, y_pos + 4), color, -1)
            cv2.putText(result, label, (34, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Determine target heatmaps directory
        save_dir = "uploads/heatmaps"
        if os.path.exists("backend/uploads") and not os.path.exists("uploads"):
            save_dir = "backend/uploads/heatmaps"

        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(image_path) if isinstance(image_path, str) else "heatmap.jpg"
        base_name, ext = os.path.splitext(filename)
        if ext.lower() in [".jfif", ""]:
            filename = f"{base_name}.jpg"
        heatmap_path = f"{save_dir}/heatmap_{filename}"
        cv2.imwrite(heatmap_path, result)

        return f"uploads/heatmaps/heatmap_{filename}"

    except Exception as e:
        print(f"Heatmap generation error: {e}")
        return image_path