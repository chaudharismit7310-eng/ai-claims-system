import spacy

nlp = None

def load_nlp():
    global nlp
    try:
        nlp = spacy.load("en_core_web_sm")
        print("[OK] spaCy en_core_web_sm pipeline loaded successfully!")
    except Exception as e:
        print(f"[WARN] Could not load spaCy en_core_web_sm: {e}")
        nlp = None

COLLISION_VERBS = {
    "hit", "crash", "ram", "collide", "strike", "smash",
    "rear-end", "scrape", "bump", "dent", "damage", "sideswipe", "skid", "lose"
}

DRIVER_SUBJECTS = {"i", "we", "my car", "my vehicle", "myself"}
OPPONENT_SUBJECTS = {"truck", "bus", "car", "lorry", "vehicle", "auto", "he", "she", "they", "driver", "someone", "taxi", "motorcycle", "bike"}
STATIONARY_OBJECTS = {"tree", "pole", "divider", "wall", "gate", "barrier", "curb", "pillar", "post", "fence", "pavement", "median"}

def analyze_fault(text: str) -> dict:
    global nlp
    if nlp is None:
        load_nlp()

    text_lower = text.lower()

    # Fallback keyword indicators
    driver_keywords = [
        "my fault", "i lost control", "i jumped signal", "i was speeding",
        "i didn't see", "i failed to brake", "i was distracted", "my mistake"
    ]
    opponent_keywords = [
        "hit me from behind", "not my fault", "they were at fault",
        "was hit by", "other vehicle crashed"
    ]
    natural_keywords = [
        "rain", "flood", "slippery", "fog", "storm",
        "landslide", "hail", "snow", "ice", "wind",
        "fallen tree", "natural disaster", "pothole", "waterlogging"
    ]
    fraud_indicators = [
        "no witness", "no camera", "late night", "empty road",
        "no one around", "middle of nowhere", "no evidence"
    ]

    linguistic_evidence = []
    entities = []
    driver_score = 0
    opponent_score = 0
    natural_score = sum(1 for kw in natural_keywords if kw in text_lower)
    fraud_flags = [kw for kw in fraud_indicators if kw in text_lower]

    # Authentic spaCy syntactic dependency and entity extraction
    if nlp is not None:
        doc = nlp(text)

        # 1. Extract Named Entities (Locations, Dates, Facilities)
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_
            })

        # 2. Extract Dependency S-V-O for collision actions
        for token in doc:
            lemma = token.lemma_.lower()
            if lemma in COLLISION_VERBS or token.pos_ == "VERB":
                subj = None
                obj = None

                # Find subject and object
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subj = child.text.lower()
                    elif child.dep_ in ("dobj", "pobj", "attr"):
                        obj = child.text.lower()
                    elif child.dep_ == "prep":
                        for prep_child in child.children:
                            if prep_child.dep_ == "pobj":
                                obj = prep_child.text.lower()

                if subj or obj:
                    relation_str = f"[{subj or 'unknown'}] -> [{token.text}] -> [{obj or 'unknown'}]"
                    linguistic_evidence.append(relation_str)

                    # Assess subject fault
                    if subj:
                        if subj in ("i", "we", "my car", "my vehicle"):
                            driver_score += 2
                            if obj and any(stat in obj for stat in STATIONARY_OBJECTS):
                                driver_score += 2
                        elif any(opp in subj for opp in OPPONENT_SUBJECTS):
                            opponent_score += 2

                    # Assess object fault
                    if obj:
                        if any(me in obj for me in ["me", "my car", "my vehicle", "our car"]):
                            if subj and any(opp in subj for opp in OPPONENT_SUBJECTS):
                                opponent_score += 2
                        elif any(stat in obj for stat in STATIONARY_OBJECTS) and subj in ("i", "we"):
                            driver_score += 2

    # Reinforce with keyword heuristics
    driver_score += sum(1 for kw in driver_keywords if kw in text_lower)
    opponent_score += sum(1 for kw in opponent_keywords if kw in text_lower)

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
            "linguistic_evidence": linguistic_evidence,
            "entities": entities,
            "fraud_indicators": fraud_flags
        }

    if max_score == 1:
        confidence = 0.70
    elif max_score <= 3:
        confidence = 0.84
    else:
        confidence = 0.94

    return {
        "fault": max_fault,
        "confidence": round(confidence, 2),
        "linguistic_evidence": linguistic_evidence,
        "entities": entities,
        "fraud_indicators": fraud_flags
    }