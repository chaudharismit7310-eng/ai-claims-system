import hashlib
import os
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import io


def compute_dhash(image_path: str, hash_size: int = 8) -> str:
    """
    Perceptual difference hashing (dHash) using PIL and NumPy.
    Produces a 64-bit perceptual visual hash resistant to re-compression,
    format conversion, and resizing.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and resize to (width=hash_size+1, height=hash_size)
            gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = np.asarray(gray)
            # Compare adjacent pixels in each row (8 rows * 8 comparisons = 64 bits)
            diff = pixels[:, 1:] > pixels[:, :-1]
            decimal_value = 0
            for bit in diff.flatten():
                decimal_value = (decimal_value << 1) | int(bit)
            return f"{decimal_value:016x}"
    except Exception as e:
        print(f"dHash computation error: {e}")
        try:
            # Fallback to byte hash if image decode fails
            with open(image_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Computes bitwise Hamming distance between two hexadecimal hash strings.
    A distance <= 5 indicates a perceptual duplicate image.
    """
    try:
        if not hash1 or not hash2:
            return 999
        v1 = int(hash1, 16)
        v2 = int(hash2, 16)
        return bin(v1 ^ v2).count("1")
    except Exception:
        return 999


# Backward compatible alias
get_image_hash = compute_dhash


def perform_ela(image_path: str, quality: int = 90) -> float:
    """
    Error Level Analysis — detects edited/manipulated images

    Returns:
        ela_score (0-1)
    """

    try:

        original = Image.open(image_path).convert('RGB')

        # Save compressed image
        buffer = io.BytesIO()

        original.save(
            buffer,
            'JPEG',
            quality=quality
        )

        buffer.seek(0)

        compressed = Image.open(buffer).convert('RGB')

        # Difference
        diff = ImageChops.difference(
            original,
            compressed
        )

        # Enhance
        enhancer = ImageEnhance.Brightness(diff)

        diff_enhanced = enhancer.enhance(10)

        # Score
        diff_array = np.array(diff_enhanced)

        ela_score = float(
            np.mean(diff_array)
        ) / 255.0

        return round(ela_score, 4)

    except Exception as e:

        print(f"ELA error: {e}")

        return 0.0


def check_image_fraud(
    image_path: str,
    db=None,
    current_claim_id: int = None
) -> dict:
    """
    Base image fraud checks:
    1. Duplicate image via perceptual difference hashing (dHash)
    2. ELA manipulation
    3. File size
    4. Dimensions
    """

    results = {
        "image_hash": "",
        "ela_score": 0.0,
        "is_duplicate": False,
        "is_edited": False,
        "is_suspicious": False,
        "fraud_reasons": [],
        "fraud_score_addition": 0.0
    }

    # --------------------------------------------------
    # 1. PERCEPTUAL IMAGE HASH (dHash)
    # --------------------------------------------------

    img_hash = compute_dhash(image_path)

    results["image_hash"] = img_hash

    # --------------------------------------------------
    # 2. DUPLICATE CHECK (Hamming distance comparison)
    # --------------------------------------------------

    if db and img_hash:

        from app.models.claim_model import Claim

        existing_claims = db.query(Claim).filter(
            Claim.image_hash.isnot(None),
            Claim.image_hash != ""
        ).all()

        for existing in existing_claims:
            if current_claim_id is not None and existing.claim_id == current_claim_id:
                continue

            dist = hamming_distance(img_hash, existing.image_hash)
            # Distance <= 5 indicates visually identical image (even if resized or compressed)
            if existing.image_hash == img_hash or dist <= 5:
                results["is_duplicate"] = True
                results["is_suspicious"] = True

                match_label = "Perceptual Visual Match" if dist > 0 else "Exact Match"
                results["fraud_reasons"].append(
                    f"DUPLICATE IMAGE ({match_label}, Hamming dist={dist}): Visually identical image used in Claim #{existing.claim_id}"
                )

                results["fraud_score_addition"] += 0.40
                break


    # --------------------------------------------------
    # 3. ELA ANALYSIS
    # --------------------------------------------------

    ela_score = perform_ela(image_path)

    results["ela_score"] = ela_score

    # LOW ELA
    if ela_score < 0.01:

        results["is_edited"] = True
        results["is_suspicious"] = True

        results["fraud_reasons"].append(
            "LOW ELA SCORE: Image may be downloaded from internet or stock photo"
        )

        results["fraud_score_addition"] += 0.30

    # HIGH ELA
    elif ela_score > 0.15:

        results["is_edited"] = True
        results["is_suspicious"] = True

        results["fraud_reasons"].append(
            f"HIGH ELA SCORE ({ela_score}): Image appears heavily edited/manipulated"
        )

        results["fraud_score_addition"] += 0.25

    # --------------------------------------------------
    # 4. FILE SIZE CHECK
    # --------------------------------------------------

    try:

        file_size = os.path.getsize(image_path)

        if file_size < 50000:

            results["fraud_reasons"].append(
                "SMALL FILE SIZE: Image may be low-quality internet download"
            )

            results["fraud_score_addition"] += 0.10

    except:
        pass

    # --------------------------------------------------
    # 5. IMAGE DIMENSIONS
    # --------------------------------------------------

    try:

        img = Image.open(image_path)

        width, height = img.size

        if (
            width in [800, 1024, 1280, 1920]
            and
            height in [600, 768, 720, 1080]
        ):

            results["fraud_reasons"].append(
                f"STANDARD DIMENSIONS ({width}x{height}): May be stock/internet image"
            )

            results["fraud_score_addition"] += 0.10

    except:
        pass

    # --------------------------------------------------
    # FINAL REASON STRING
    # --------------------------------------------------

    results["image_fraud_reason"] = " | ".join(
        results["fraud_reasons"]
    )

    return results


def complete_image_analysis(
    image_path: str,
    db=None,
    current_claim_id: int = None
) -> dict:
    """
    Complete image fraud analysis combining:

    1. Hash duplicate detection
    2. ELA edit detection
    3. EXIF metadata analysis
    4. AI forgery detection
    """

    from app.services.ai_forgery_detection import analyze_image_with_ai
    from app.utils.exif_extractor import extract_exif

    # --------------------------------------------------
    # RUN ALL CHECKS
    # --------------------------------------------------

    hash_ela_result = check_image_fraud(
        image_path,
        db,
        current_claim_id
    )

    exif_result = extract_exif(image_path)

    ai_result = analyze_image_with_ai(image_path)

    # --------------------------------------------------
    # COMBINE FRAUD SCORES
    # --------------------------------------------------

    total_fraud_addition = (
        hash_ela_result["fraud_score_addition"]
    )

    # EXIF
    if exif_result.get("fraud_flag"):

        total_fraud_addition += 0.15

    # AI FRAUD
    total_fraud_addition += (
        ai_result["ai_fraud_score"] * 0.5
    )

    # --------------------------------------------------
    # COMBINE REASONS
    # --------------------------------------------------

    all_reasons = []

    if hash_ela_result["fraud_reasons"]:

        all_reasons.extend(
            hash_ela_result["fraud_reasons"]
        )

    if (
        exif_result.get("fraud_flag")
        and
        exif_result.get("fraud_reason")
    ):

        all_reasons.append(
            f"EXIF: {exif_result['fraud_reason']}"
        )

    if ai_result["ai_fraud_reason"]:

        all_reasons.append(
            ai_result["ai_fraud_reason"]
        )

    # --------------------------------------------------
    # OVERALL SUSPICIOUS
    # --------------------------------------------------

    is_suspicious = (
        hash_ela_result["is_suspicious"]
        or
        exif_result.get("fraud_flag", False)
        or
        ai_result["ai_fraud_score"] > 0.3
    )

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    return {
        "image_hash": hash_ela_result["image_hash"],

        "ela_score": hash_ela_result["ela_score"],

        "is_duplicate": hash_ela_result["is_duplicate"],

        "is_edited": hash_ela_result["is_edited"],

        "is_real_accident": ai_result["is_real_accident"],

        "ai_fraud_score": ai_result["ai_fraud_score"],

        "real_probability": ai_result.get(
            "real_probability",
            0
        ),

        "fake_probability": ai_result.get(
            "fake_probability",
            0
        ),

        "exif_fraud_flag": exif_result.get(
            "fraud_flag",
            False
        ),

        "exif_timestamp": exif_result.get(
            "timestamp"
        ),

        "is_suspicious": is_suspicious,

        "fraud_score_addition": round(
            min(total_fraud_addition, 0.6),
            2
        ),

        "image_fraud_reason": " | ".join(all_reasons)
    }