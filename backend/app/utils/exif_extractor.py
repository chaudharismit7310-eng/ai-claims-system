from PIL import Image
from PIL.ExifTags import TAGS
import json
from datetime import datetime

def extract_exif(image_path: str) -> dict:
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()

        if not exif_data:
            return {
                "has_exif": False,
                "fraud_flag": True,
                "fraud_reason": "No EXIF metadata found - image may be edited",
                "timestamp": None,
                "gps": None
            }

        readable = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            readable[tag] = str(value)

        # Timestamp check
        timestamp = readable.get("DateTime") or readable.get("DateTimeOriginal")

        # GPS check
        gps_info = readable.get("GPSInfo")

        # Fraud checks
        fraud_flag = False
        fraud_reason = ""

        if not timestamp:
            fraud_flag = True
            fraud_reason = "Missing timestamp in image metadata"

        if timestamp:
            try:
                img_date = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
                days_old = (datetime.now() - img_date).days
                if days_old > 30:
                    fraud_flag = True
                    fraud_reason = f"Image is {days_old} days old - possible reuse"
            except:
                pass

        return {
            "has_exif": True,
            "fraud_flag": fraud_flag,
            "fraud_reason": fraud_reason,
            "timestamp": timestamp,
            "gps": gps_info,
            "raw_data": json.dumps(readable)[:500]
        }

    except Exception as e:
        return {
            "has_exif": False,
            "fraud_flag": True,
            "fraud_reason": f"Could not read image metadata: {str(e)}",
            "timestamp": None,
            "gps": None
        }