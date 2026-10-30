import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.plate_normalizer import normalize_plate
from app.services.consistency_checker import check_claim_consistency

def test_normalize_plate():
    print("======================================================================")
    print("RUNNING LICENSE PLATE NORMALIZATION TESTS")
    print("======================================================================\n")

    test_cases = [
        ("MH 43 D 3193", "MH.43.D.3193", True, "Spaces vs Dots"),
        ("MH 43 D 3193", "MH-43-D-3193", True, "Spaces vs Hyphens"),
        ("MH_43_D_3193", "mh.43.d.3193", True, "Underscores & Lowercase vs Dots"),
        ("TN-01-AM-6142", "TN.01.AM.6142", True, "Indian Plate Hyphens vs Dots"),
        ("MH 43 D 3193", "MH 43 D 3194", False, "Different Plate Numbers"),
        ("", "MH 43 D 3193", False, "Empty String"),
        (None, "MH 43 D 3193", False, "None Input"),
    ]

    for reg, ocr, should_match, description in test_cases:
        norm_reg = normalize_plate(reg)
        norm_ocr = normalize_plate(ocr)
        matches = (norm_reg == norm_ocr) if norm_reg and norm_ocr else False

        print(f"Test: {description}")
        print(f"   Registered: '{reg}'  --> Normalized: '{norm_reg}'")
        print(f"   Detected  : '{ocr}'  --> Normalized: '{norm_ocr}'")
        print(f"   Match Result: {matches} (Expected: {should_match})")
        assert matches == should_match, f"FAILED: '{reg}' vs '{ocr}' expected match={should_match}, got {matches}"
        print("   [OK] PASSED!\n")

    # Integration test with check_claim_consistency
    print("Testing consistency_checker with dot vs space plate formats...")
    consistency_res = check_claim_consistency(
        description="Damage on front bumper.",
        detections=[{"class": "bumper_damage", "confidence": 0.8}],
        claim_amount=15000.0,
        claim_data={"vehicle_number": "MH 43 D 3193"},
        ocr_text="MH.43.D.3193"
    )

    issues = consistency_res.get("issues", [])
    has_plate_mismatch = any(i.get("type") == "LICENSE_PLATE_MISMATCH" for i in issues)
    print(f"   Consistency Issues: {issues}")
    print(f"   Plate Mismatch Flagged: {has_plate_mismatch}")
    assert not has_plate_mismatch, "FALSE POSITIVE ERROR: 'MH 43 D 3193' vs 'MH.43.D.3193' should NOT trigger LICENSE_PLATE_MISMATCH!"
    print("   [OK] Consistency Checker Integration Test PASSED!\n")

    print("======================================================================")
    print("ALL LICENSE PLATE NORMALIZATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    test_normalize_plate()
