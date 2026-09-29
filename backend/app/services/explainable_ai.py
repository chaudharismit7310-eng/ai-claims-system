def generate_explanation(
    fraud_score: float,
    fault_type: str,
    consistency_score: float,
    consistency_issues: list,
    exif_fraud_flag: bool,
    image_fraud_reason: str,
    claim_amount: float,
    estimated_cost: float,
    ela_score: float,
    damage_severity: str,
    **kwargs
) -> dict:

    """
    Generate dynamic Explainable AI (XAI) breakdown of risk factors.
    Computes proportional contributions calibrated to the actual predicted fraud score.
    """
    raw_factors = []

    # 1. Perceptual Duplicate Detection
    if "DUPLICATE" in image_fraud_reason:
        raw_factors.append({
            "factor": "Duplicate Image Submission",
            "weight": 0.40,
            "severity": "CRITICAL",
            "icon": "🔴",
            "detail": "Perceptual hash matched a photo from a previous claim in the database."
        })

    # 2. AI Forgery / Generated Photo Detection (CLIP)
    if "AI DETECTED" in image_fraud_reason or "FORGERY" in image_fraud_reason:
        raw_factors.append({
            "factor": "AI Forgery / Stock Photo",
            "weight": 0.35,
            "severity": "HIGH",
            "icon": "🔴",
            "detail": "Zero-shot CLIP visual inspection detected synthetic or internet-sourced patterns."
        })

    # 3. Error Level Analysis (ELA) Compression Discrepancy
    if ela_score > 0.15:
        raw_factors.append({
            "factor": "High Compression Disparity (ELA)",
            "weight": round(min(0.30, float(ela_score) * 1.8), 2),
            "severity": "HIGH",
            "icon": "🟠",
            "detail": f"ELA score of {ela_score:.4f} indicates localized digital editing or re-saving."
        })
    elif ela_score < 0.008 and ela_score > 0:
        raw_factors.append({
            "factor": "Low ELA Signature",
            "weight": 0.20,
            "severity": "MEDIUM",
            "icon": "🟡",
            "detail": f"Extremely uniform ELA score ({ela_score:.4f}) suggests web-compressed stock imagery."
        })

    # 4. EXIF Metadata Tampering
    if exif_fraud_flag:
        raw_factors.append({
            "factor": "EXIF Metadata Tampering",
            "weight": 0.22,
            "severity": "HIGH",
            "icon": "🟠",
            "detail": "Metadata contains image editing software signatures or conflicting dates."
        })

    # 5. Narrative & Vision Inconsistency
    if consistency_score < 0.70:
        inconsistency_weight = round((1.0 - consistency_score) * 0.40, 2)
        raw_factors.append({
            "factor": "Narrative-Vision Contradiction",
            "weight": inconsistency_weight,
            "severity": "HIGH" if consistency_score < 0.40 else "MEDIUM",
            "icon": "🟠" if consistency_score < 0.40 else "🟡",
            "detail": f"Reported damage description conflicts with YOLO/VLM detections (consistency: {consistency_score:.0%})."
        })

    # 6. Repair Cost Overcharge
    if claim_amount > 0 and estimated_cost > 0:
        overcharge_ratio = (claim_amount - estimated_cost) / claim_amount
        if overcharge_ratio > 0.35:
            overcharge_weight = round(min(0.25, overcharge_ratio * 0.30), 2)
            raw_factors.append({
                "factor": "Excessive Repair Cost Claimed",
                "weight": overcharge_weight,
                "severity": "HIGH" if overcharge_ratio > 0.60 else "MEDIUM",
                "icon": "🟠" if overcharge_ratio > 0.60 else "🟡",
                "detail": f"Claimed ₹{claim_amount:,.0f} vs AI estimate of ₹{estimated_cost:,.0f} ({overcharge_ratio:.0%} variance)."
            })

    # 7. Driver Fault Admission
    if fault_type == "driver_fault":
        raw_factors.append({
            "factor": "Driver Admitted Fault",
            "weight": 0.15,
            "severity": "MEDIUM",
            "icon": "🟡",
            "detail": "Linguistic analysis of incident statement identified driver responsibility."
        })

    # 8. Garage Audit Gross Inflation
    garage_audit_json = kwargs.get("garage_audit_json")
    if garage_audit_json:
        import json
        try:
            audit = json.loads(garage_audit_json)
            if audit.get("audit_verdict") == "GROSSLY_INFLATED":
                raw_factors.append({
                    "factor": "Fabricated / Inflated Garage Estimate Detected",
                    "weight": 0.28,
                    "severity": "CRITICAL",
                    "icon": "🔴",
                    "detail": f"Garage quoted ₹{audit.get('total_quoted_cost')} vs AI Baseline ₹{audit.get('ai_reconciled_cost')} ({audit.get('inflation_percentage')}% variance)."
                })
        except Exception:
            pass

    # 9. Unexplained Geographic Contradiction
    is_post_transit = bool(kwargs.get("is_post_transit", False))
    incident_location = kwargs.get("incident_location")
    inspection_location = kwargs.get("inspection_location")
    transit_reason = kwargs.get("transit_reason")
    geo_discrepancy_detected = bool(kwargs.get("geo_discrepancy_detected", False))

    if not is_post_transit and (geo_discrepancy_detected or "Undeclared Geographic Discrepancy" in image_fraud_reason):
        raw_factors.append({
            "factor": "Unexplained Geographic Contradiction",
            "weight": 0.30,
            "severity": "CRITICAL",
            "icon": "🔴",
            "detail": "Incident location contradicts photo telemetry without post-transit declaration."
        })

    # 10. Decoupled Camera EXIF GPS & VLM Scene Incongruity
    exif_gps_status = kwargs.get("exif_gps_status", "METADATA_STRIPPED")
    is_live_capture = bool(kwargs.get("is_live_capture", False))
    geographic_incongruity = bool(kwargs.get("geographic_incongruity", False))
    geographic_incongruity_reason = kwargs.get("geographic_incongruity_reason", "NONE")

    if exif_gps_status == "METADATA_STRIPPED" and not is_live_capture:
        raw_factors.append({
            "factor": "Missing / Stripped Camera EXIF GPS",
            "weight": 0.25,
            "severity": "HIGH",
            "icon": "🟠",
            "detail": "Photo lacks authentic camera hardware GPS metadata. Browser submission GPS was decoupled."
        })

    if geographic_incongruity:
        raw_factors.append({
            "factor": "Non-Indian Scene Detected (Geographic Fraud)",
            "weight": 0.35,
            "severity": "CRITICAL",
            "icon": "🔴",
            "detail": f"VLM visual inspection detected foreign roadway/vehicle infrastructure ({geographic_incongruity_reason})."
        })

    # Normalize contributions dynamically to match the overall fraud risk
    total_weight = sum(f["weight"] for f in raw_factors)
    factors = []

    if total_weight > 0:
        target_risk = max(0.05, float(fraud_score))
        for f in raw_factors:
            # Proportional contribution relative to total risk
            normalized_contrib = round((f["weight"] / total_weight) * target_risk, 3)
            factors.append({
                "factor": f["factor"],
                "contribution": normalized_contrib,
                "percentage": f"{round((f['weight'] / total_weight) * 100)}%",
                "severity": f["severity"],
                "icon": f["icon"],
                "detail": f["detail"]
            })
    else:
        factors.append({
            "factor": "Baseline Claim Profile",
            "contribution": round(max(0.05, float(fraud_score)), 3),
            "percentage": "100%",
            "severity": "LOW",
            "icon": "🟢",
            "detail": "Claim exhibits standard risk characteristics with no digital or narrative tampering detected."
        })

    # Sort descending by contribution
    factors.sort(key=lambda x: x["contribution"], reverse=True)

    # Prepend authentic camera EXIF GPS trusted badge if hardware verified
    if exif_gps_status == "HARDWARE_VERIFIED":
        c_lat = kwargs.get("photo_capture_lat")
        c_lon = kwargs.get("photo_capture_lon")
        gps_str = f"Lat: {c_lat:.4f}, Long: {c_lon:.4f}" if c_lat is not None and c_lon is not None else "GPS coordinates present"
        factors.insert(0, {
            "factor": "Authentic Camera EXIF GPS Verified",
            "contribution": 0.0,
            "percentage": "Verified",
            "severity": "TRUSTED",
            "icon": "📡",
            "detail": f"Camera hardware EXIF metadata verified ({gps_str})."
        })

    # Prepend post-transit inspection declaration badge if declared
    if is_post_transit:
        inc_loc_str = incident_location or 'Declared Incident Site'
        insp_loc_str = inspection_location or 'Current Inspection Site'
        reason_str = transit_reason or 'Vehicle moved prior to inspection'
        factors.insert(0, {
            "factor": "Declared Post-Transit Inspection",
            "contribution": 0.0,
            "percentage": "Verified",
            "severity": "TRUSTED",
            "icon": "📋",
            "detail": f"Customer declared post-transit movement ({reason_str}). Incident at {inc_loc_str}, inspected at {insp_loc_str}."
        })

    # Prepend positive verification badge if live hardware capture was used
    is_live_capture = bool(kwargs.get("is_live_capture", False))
    if is_live_capture:
        lat = kwargs.get("device_latitude")
        lng = kwargs.get("device_longitude")
        ts = kwargs.get("capture_timestamp")
        gps_detail = f"Lat: {lat:.4f}, Long: {lng:.4f}" if lat is not None and lng is not None else "GPS coordinates acquired"
        factors.insert(0, {
            "factor": "Live Hardware Capture Verified",
            "contribution": 0.0,
            "percentage": "Verified",
            "severity": "TRUSTED",
            "icon": "🛡️",
            "detail": f"Physical presence verified via live camera lock & geolocation ({gps_detail}, Timestamp: {ts or 'UTC'})."
        })
        
    garage_audit_json = kwargs.get("garage_audit_json")
    if garage_audit_json:
        import json
        try:
            audit = json.loads(garage_audit_json)
            verdict = audit.get("audit_verdict")
            if verdict == "FAIR":
                factors.insert(0, {
                    "factor": "Garage Estimate Reconciled & Fair",
                    "contribution": 0.0,
                    "percentage": "Verified",
                    "severity": "TRUSTED",
                    "icon": "📋",
                    "detail": "Line-item breakdown aligns with AI OEM baselines (<10% variance)."
                })
        except Exception:
            pass

    walkaround_video_url = kwargs.get("walkaround_video_url")
    if walkaround_video_url:
        factors.insert(0, {
            "factor": "360° Inspection Video Provided",
            "contribution": 0.0,
            "percentage": "Verified",
            "severity": "TRUSTED",
            "icon": "📹",
            "detail": "Cross-Verification Enabled. Video proof of vehicle condition and environment available."
        })


    # Risk level categorization
    if fraud_score >= 0.70:
        risk_level = "CRITICAL"
        risk_color = "red"
        risk_message = "High probability of fraudulent claim — immediate investigation required."
    elif fraud_score >= 0.50:
        risk_level = "HIGH"
        risk_color = "orange"
        risk_message = "Multiple suspicious forensic indicators detected — senior adjuster review recommended."
    elif fraud_score >= 0.30:
        risk_level = "MEDIUM"
        risk_color = "yellow"
        risk_message = "Moderate risk indicators observed — standard verification advised."
    else:
        risk_level = "LOW"
        risk_color = "green"
        risk_message = "Claim appears genuine and consistent with reported incident."

    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_message": risk_message,
        "fraud_score": round(fraud_score, 2),
        "factors": factors,
        "total_factors": len(factors),
        "top_reason": factors[0]["factor"] if factors else "Standard Low Risk"
    }