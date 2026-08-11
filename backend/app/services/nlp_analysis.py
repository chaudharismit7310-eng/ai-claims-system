import spacy

nlp = None

def load_nlp():
    global nlp
    try:
        nlp = spacy.load("en_core_web_sm")
        print("spaCy loaded!")
    except:
        nlp = None

def analyze_fault(text: str) -> dict:
    global nlp
    if nlp is None:
        load_nlp()

    text_lower = text.lower()

    driver_keywords = [
        "my fault", "i hit", "i crashed", "i lost control",
        "i jumped signal", "i was speeding", "i was drunk",
        "i didn't see", "i failed to brake", "i was distracted",
        "my mistake", "i caused", "i ran", "i skipped"
    ]

    opponent_keywords = [
        "other car hit", "not my fault", "he hit", "she hit",
        "truck hit", "bus hit", "other driver", "they crashed",
        "hit me from behind", "hit from side", "opponent",
        "other vehicle", "they were at fault", "another car",
        "someone hit", "was hit by"
    ]

    natural_keywords = [
        "rain", "flood", "slippery", "fog", "storm",
        "landslide", "hail", "snow", "ice", "wind",
        "fallen tree", "natural disaster", "weather",
        "pothole", "road condition"
    ]

    fraud_indicators = [
        "no witness", "no camera", "late night", "empty road",
        "no one around", "middle of nowhere", "no evidence"
    ]

    driver_score = sum(1 for kw in driver_keywords if kw in text_lower)
    opponent_score = sum(1 for kw in opponent_keywords if kw in text_lower)
    natural_score = sum(1 for kw in natural_keywords if kw in text_lower)
    fraud_flags = [kw for kw in fraud_indicators if kw in text_lower]

    scores = {
        "driver_fault": driver_score,
        "opponent_fault": opponent_score,
        "natural": natural_score
    }

    max_fault = max(scores, key=scores.get)
    max_score = scores[max_fault]

    if max_score == 0:
        return {
            "fault": "unclear",
            "confidence": 0.50,
            "fraud_indicators": fraud_flags
        }

    if max_score == 1:
        confidence = 0.70
    elif max_score == 2:
        confidence = 0.82
    else:
        confidence = 0.92

    return {
        "fault": max_fault,
        "confidence": confidence,
        "fraud_indicators": fraud_flags
    }