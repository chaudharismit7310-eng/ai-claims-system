from datetime import datetime

def estimate_repair_cost(
    vehicle_details: dict,
    damage_detections: list,
    vlm_severity: str = "moderate"
) -> dict:
    """
    Calculates objective vehicle repair costs strictly from physical damage
    and vehicle attributes, completely independent of claimant-declared numbers.
    """
    base_val = float(vehicle_details.get("price", 800000.0))
    current_year = datetime.now().year
    vehicle_year = int(vehicle_details.get("year", current_year - 4))
    vehicle_age = max(0, current_year - vehicle_year)

    # 1. Base severity multiplier
    severity_weights = {
        "minor": 0.03,
        "moderate": 0.08,
        "severe": 0.18
    }
    sev_factor = severity_weights.get(vlm_severity.lower(), 0.06)

    # 2. Panel and damage instance multiplier
    damage_count = len(damage_detections)
    panel_multiplier = 1.0 + 0.15 * max(0, damage_count - 1)

    # Damage classes and spatial footprint adjustment (if bboxes present)
    class_weights = {
        "broken_part": 1.25,
        "broken_glass": 1.20,
        "headlight_damage": 1.15,
        "taillight_damage": 1.10,
        "bumper_damage": 1.10,
        "dent": 1.05,
        "scratch": 0.90,
        "paint_damage": 0.90,
        "crack": 1.00,
        "corrosion": 0.95
    }
    if damage_detections:
        cls_factors = []
        total_bbox_area = 0.0
        for d in damage_detections:
            if isinstance(d, dict):
                cname = str(d.get("class", d.get("label", ""))).lower()
                cls_factors.append(class_weights.get(cname, 1.0))
                bbox = d.get("bbox")
                if bbox and len(bbox) >= 4:
                    w = max(0.0, float(bbox[2]) - float(bbox[0]))
                    h = max(0.0, float(bbox[3]) - float(bbox[1]))
                    total_bbox_area += (w * h)
            else:
                cls_factors.append(1.0)

        if cls_factors:
            avg_cls = sum(cls_factors) / len(cls_factors)
            panel_multiplier *= avg_cls

        if total_bbox_area > 0:
            footprint_scale = min(1.25, max(0.95, 1.0 + (total_bbox_area / 2000000.0) * 0.15))
            panel_multiplier *= footprint_scale

    # 3. Age-based depreciation discount on parts
    depreciation = 1.0 - 0.04 * min(10, vehicle_age)

    # 4. Objective repair estimation formula
    raw_estimate = base_val * sev_factor * panel_multiplier * depreciation

    # 5. Clamp to realistic discrete repair bands based on severity
    if vlm_severity.lower() == "minor":
        bounded_min = max(3000.0, raw_estimate * 0.85)
        bounded_max = min(20000.0, raw_estimate * 1.15)
    elif vlm_severity.lower() == "moderate":
        bounded_min = max(20000.0, raw_estimate * 0.85)
        bounded_max = min(60000.0, raw_estimate * 1.15)
    else:  # severe
        bounded_min = max(60000.0, raw_estimate * 0.85)
        bounded_max = max(bounded_min + 15000.0, raw_estimate * 1.20)

    predicted_cost = round(float(min(bounded_max, max(bounded_min, (bounded_min + bounded_max) / 2.0))), 2)

    return {
        "predicted_cost": predicted_cost,
        "cost_range_min": round(bounded_min, 2),
        "cost_range_max": round(bounded_max, 2)
    }
