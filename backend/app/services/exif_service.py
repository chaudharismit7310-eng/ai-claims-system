from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Any, Optional

def convert_to_degrees(value) -> Optional[float]:
    """
    Helper to convert the GPS coordinates stored in EXIF to decimal degrees
    Handles rational tuples, IFDRational, floats, ints, etc.
    """
    try:
        def to_float(x):
            if isinstance(x, tuple) and len(x) == 2:
                return float(x[0]) / float(x[1]) if x[1] != 0 else 0.0
            if hasattr(x, 'numerator') and hasattr(x, 'denominator'):
                return float(x.numerator) / float(x.denominator) if x.denominator != 0 else 0.0
            return float(x)

        d = to_float(value[0])
        m = to_float(value[1])
        s = to_float(value[2])

        return d + (m / 60.0) + (s / 3600.0)
    except Exception as e:
        print(f"Error converting GPS degrees: {e}")
        return None

def extract_exif_telemetry(image_path: str) -> Dict[str, Any]:
    """
    Decoupled Photo Capture Telemetry Extractor.
    Extracts authentic camera GPS metadata (lat, lon) directly from EXIF headers.
    Returns status 'HARDWARE_VERIFIED' if camera GPS exists, else 'METADATA_STRIPPED'.
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()

        if not exif_data:
            return {
                "has_exif_gps": False,
                "capture_lat": None,
                "capture_lon": None,
                "status": "METADATA_STRIPPED"
            }

        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for gps_tag_id in value:
                    sub_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[sub_tag] = value[gps_tag_id]

        if not gps_info:
            return {
                "has_exif_gps": False,
                "capture_lat": None,
                "capture_lon": None,
                "status": "METADATA_STRIPPED"
            }

        lat_raw = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon_raw = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if lat_raw and lat_ref and lon_raw and lon_ref:
            lat = convert_to_degrees(lat_raw)
            lon = convert_to_degrees(lon_raw)

            if lat is not None and lon is not None:
                if str(lat_ref).upper() == "S":
                    lat = -lat
                if str(lon_ref).upper() == "W":
                    lon = -lon

                return {
                    "has_exif_gps": True,
                    "capture_lat": round(lat, 6),
                    "capture_lon": round(lon, 6),
                    "status": "HARDWARE_VERIFIED"
                }

        return {
            "has_exif_gps": False,
            "capture_lat": None,
            "capture_lon": None,
            "status": "METADATA_STRIPPED"
        }

    except Exception as e:
        print(f"EXIF Telemetry extraction exception: {e}")
        return {
            "has_exif_gps": False,
            "capture_lat": None,
            "capture_lon": None,
            "status": "METADATA_STRIPPED"
        }
