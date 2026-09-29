import os
from PIL import Image, ImageOps
from typing import Optional, Tuple, Dict, Any

SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "BMP", "TIFF"}

def validate_image(image_path: str) -> Dict[str, Any]:
    """
    Validates image file existence, format, and readable pixel buffer.
    """
    if not os.path.exists(image_path):
        return {"valid": False, "error": "File does not exist"}

    try:
        with Image.open(image_path) as img:
            img.verify()

        # Reopen to read dimensions (verify() closes or invalidates file pointer)
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = img.format.upper() if img.format else "UNKNOWN"

        if width < 50 or height < 50:
            return {"valid": False, "error": "Image resolution too low (minimum 50x50 pixels)"}

        return {
            "valid": True,
            "width": width,
            "height": height,
            "format": img_format,
            "is_supported": img_format in SUPPORTED_FORMATS
        }
    except Exception as e:
        return {"valid": False, "error": f"Corrupted or unreadable image file: {str(e)}"}

def extract_image_properties(image_path: str) -> Dict[str, Any]:
    """
    Extracts geometric and encoding properties of the vehicle damage photograph.
    """
    try:
        file_size_bytes = os.path.getsize(image_path)
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = round(width / max(1, height), 2)
            mode = img.mode
            img_format = img.format

        return {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "color_mode": mode,
            "format": img_format,
            "size_kb": round(file_size_bytes / 1024, 1)
        }
    except Exception as e:
        return {"error": str(e)}

def preprocess_for_inference(
    image_path: str,
    max_size: int = 1280,
    output_path: Optional[str] = None
) -> str:
    """
    Normalizes image orientation, converts to RGB, and scales down if overly large
    to optimize YOLO and CLIP inference speeds while maintaining aspect ratio.
    """
    try:
        with Image.open(image_path) as img:
            # Auto-orient based on EXIF tag 274 if present
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")

            width, height = img.size
            if max(width, height) > max_size:
                scaling_factor = max_size / float(max(width, height))
                new_size = (int(width * scaling_factor), int(height * scaling_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            dest_path = output_path or image_path
            img.save(dest_path, "JPEG", quality=92)
            return dest_path
    except Exception as e:
        print(f"Preprocess error for {image_path}: {e}")
        return image_path

def crop_damage_region(
    image_path: str,
    bbox: Tuple[float, float, float, float],
    output_path: str
) -> Optional[str]:
    """
    Crops a detected damage region [x1, y1, x2, y2] and writes to output_path.
    """
    try:
        with Image.open(image_path) as img:
            x1, y1, x2, y2 = [int(c) for c in bbox]
            # Ensure coordinates are within image boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img.width, x2), min(img.height, y2)

            if x2 <= x1 or y2 <= y1:
                return None

            cropped = img.crop((x1, y1, x2, y2))
            cropped.convert("RGB").save(output_path, "JPEG", quality=90)
            return output_path
    except Exception as e:
        print(f"Crop region error: {e}")
        return None
