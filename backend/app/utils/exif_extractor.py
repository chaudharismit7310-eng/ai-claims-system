from PIL import Image
from PIL.ExifTags import TAGS
import json
from datetime import datetime, timedelta

EDITING_SOFTWARE_KEYWORDS = [
    "photoshop", "gimp", "canva", "pixlr", "picsart", "lightroom",
    "paint.net", "coreldraw", "affinity photo", "snapseed"
]

def extract_exif(image_path: str) -> dict:
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()

        # Missing EXIF is standard for web uploads, WhatsApp, Telegram, screenshots, and PNGs
        if not exif_data:
            return {
                "has_exif": False,
                "fraud_flag": False,
                "fraud_reason": "No EXIF metadata found (standard for digital/web uploads)",
                "timestamp": None,
                "gps": None
            }

        readable = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            readable[tag] = str(value)

        # Software check
        software = readable.get("Software", "")
        software_lower = software.lower()

        # Timestamp check
        timestamp = readable.get("DateTimeOriginal") or readable.get("DateTime")

        # GPS check
        gps_info = readable.get("GPSInfo")

        fraud_flag = False
        fraud_reason = ""

        # 1. Check for photo manipulation software
        for sw in EDITING_SOFTWARE_KEYWORDS:
            if sw in software_lower:
                fraud_flag = True
                fraud_reason = f"Image editing software detected in metadata: {software}"
                break

        # 2. Check for anomalous timestamps
        if timestamp and not fraud_flag:
            try:
                img_date = datetime.strptime(str(timestamp).strip()[:19], "%Y:%m:%d %H:%M:%S")
                now = datetime.now()
                # Future date check
                if img_date > now + timedelta(days=1):
                    fraud_flag = True
                    fraud_reason = f"Contradictory future timestamp detected in image metadata: {timestamp}"
                # Severe stale date check (over 180 days old)
                elif (now - img_date).days > 180:
                    fraud_flag = True
                    fraud_reason = f"Image capture date is {(now - img_date).days} days old — potential image reuse"
            except Exception:
                pass

        return {
            "has_exif": True,
            "fraud_flag": fraud_flag,
            "fraud_reason": fraud_reason,
            "software": software,
            "timestamp": timestamp,
            "gps": gps_info,
            "raw_data": json.dumps(readable)[:500]
        }

    except Exception as e:
        return {
            "has_exif": False,
            "fraud_flag": False,
            "fraud_reason": f"Could not read image metadata: {str(e)}",
            "timestamp": None,
            "gps": None
        }