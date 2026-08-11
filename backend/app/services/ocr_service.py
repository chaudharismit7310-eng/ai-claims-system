import easyocr
import re

reader = None

def get_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en'], gpu=False)
    return reader

def extract_number_plate(image_path: str) -> dict:
    try:
        r = get_reader()
        results = r.readtext(image_path)
        
        plate_pattern = re.compile(r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}')
        
        all_text = []
        detected_plate = None
        
        for (bbox, text, confidence) in results:
            clean_text = text.upper().replace(" ", "")
            all_text.append({"text": clean_text, "confidence": round(confidence, 2)})
            
            if plate_pattern.match(clean_text):
                detected_plate = {"plate": clean_text, "confidence": round(confidence, 2)}
        
        return {
            "detected_plate": detected_plate,
            "all_text_found": all_text,
            "plate_found": detected_plate is not None
        }
    
    except Exception as e:
        return {
            "detected_plate": None,
            "all_text_found": [],
            "plate_found": False,
            "error": str(e)
        }