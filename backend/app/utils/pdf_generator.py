from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os
import json

def generate_claim_pdf(claim) -> str:
    os.makedirs("reports", exist_ok=True)
    file_path = f"reports/claim_{claim.claim_id}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("AI Claims Validation System", styles['Title']))
    elements.append(Paragraph(f"Claim Report — #{claim.claim_id}", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Claim Details Table
    data = [
        ["Field", "Details"],
        ["Claim ID", str(claim.claim_id)],
        ["Customer Name", claim.customer_name],
        ["Car Model", claim.car_model],
        ["City", claim.city],
        ["Policy Type", claim.policy_type],
        ["Claim Amount", f"Rs. {claim.claim_amount}"],
        ["Description", claim.description or ""],
        ["", ""],
        ["AI Analysis", ""],
        ["Fault Type", claim.fault_type],
        ["Fault Confidence", str(claim.fault_confidence)],
        ["Fraud Score", str(claim.fraud_score)],
        ["Number Plate", claim.number_plate],
        ["Estimated Cost", f"Rs. {claim.estimated_cost}"],
        ["Cost Flag", claim.cost_flag],
        ["", ""],
        ["Decision", ""],
        ["AI Decision", claim.ai_decision],
        ["AI Reason", claim.ai_reason],
        ["Final Decision", claim.final_decision],
        ["Approved Amount", f"Rs. {claim.approved_amount}"],
        ["Agent Notes", claim.agent_notes or ""],
        ["Review Status", claim.review_status],
        ["", ""],
        ["Hardware Capture & Location Proof", ""],
        ["Live Capture Verification", "VERIFIED (In-App Live Camera Lock)" if getattr(claim, "is_live_capture", False) else "STANDARD (File / Gallery Upload)"],
        ["Photo Capture GPS (Camera EXIF)", f"Lat: {claim.photo_capture_lat}, Long: {claim.photo_capture_lon}" if getattr(claim, "photo_capture_lat", None) is not None else "METADATA_STRIPPED (No EXIF GPS)"],
        ["Submission Device GPS (Browser)", f"Lat: {claim.submission_device_lat or claim.device_latitude}, Long: {claim.submission_device_lon or claim.device_longitude}" if (getattr(claim, "submission_device_lat", None) or getattr(claim, "device_latitude", None)) is not None else "Not Provided"],
        ["EXIF Telemetry Status", str(getattr(claim, "exif_gps_status", "METADATA_STRIPPED"))],
        ["VLM Scene Incongruity Audit", f"REJECTED: Non-Indian Scene ({claim.geographic_incongruity_reason})" if getattr(claim, "geographic_incongruity", False) else "PASSED (Indian Roadway Environment)"],
        ["Capture Timestamp", str(getattr(claim, "capture_timestamp", None) or "Not Recorded")],
        ["360° Walkaround Video", "Attached & Verified" if getattr(claim, "walkaround_video_url", None) else "Not Provided"],
        ["", ""],
        ["Inspection & Transit Profile", "POST-TRANSIT INSPECTION (DECLARED)" if getattr(claim, "is_post_transit", False) else "ON-SCENE INSPECTION (NOT DECLARED)"],
        ["Declared Incident Site", str(getattr(claim, "incident_location", None) or "N/A (On-scene)")],
        ["Inspection / Holding Site", str(getattr(claim, "inspection_location", None) or "N/A (On-scene)")],
        ["Transit Reason", str(getattr(claim, "transit_reason", None) or "N/A (On-scene)")],
        ["Adjudication Protocol Note", "On-scene telemetry bypassed per declared safe transit protocol." if getattr(claim, "is_post_transit", False) else "Standard telemetry protocol applied."],
    ]

    table = Table(data, colWidths=[180, 320])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 9), (-1, 9), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 9), (-1, 9), colors.white),
        ('BACKGROUND', (0, 17), (-1, 17), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 17), (-1, 17), colors.white),
        ('BACKGROUND', (0, 25), (-1, 25), colors.HexColor('#8e44ad')),
        ('TEXTCOLOR', (0, 25), (-1, 25), colors.white),
        ('BACKGROUND', (0, 31), (-1, 31), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 31), (-1, 31), colors.white),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))


    elements.append(table)
    elements.append(Spacer(1, 20))
    
    if getattr(claim, "garage_audit_json", None):
        try:
            audit = json.loads(claim.garage_audit_json)
            if audit.get("flagged_items"):
                elements.append(Paragraph("Garage Quotation Line-Item Forensic Audit", styles['Heading3']))
                audit_data = [["Part / Labor", "Quoted (Rs)", "AI Baseline (Rs)", "Status"]]
                
                for item in audit.get("flagged_items", []):
                    status = f"INFLATED (+{item.get('inflation_percentage')}%)" if item.get('is_inflated') else "FAIR"
                    audit_data.append([
                        item.get('part_or_labor', '')[:40],
                        str(item.get('quoted_amount', 0)),
                        str(item.get('ai_benchmark_amount', 0)),
                        status
                    ])
                
                audit_table = Table(audit_data, colWidths=[200, 100, 100, 100])
                audit_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef9e7')]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                
                for i, item in enumerate(audit.get("flagged_items", [])):
                    if item.get("is_inflated"):
                        audit_table.setStyle(TableStyle([('TEXTCOLOR', (3, i+1), (3, i+1), colors.red)]))
                    else:
                        audit_table.setStyle(TableStyle([('TEXTCOLOR', (3, i+1), (3, i+1), colors.green)]))

                elements.append(audit_table)
                elements.append(Spacer(1, 20))
        except Exception as e:
            print(f"Error generating audit table: {e}")

    if getattr(claim, "final_approved_amount", None) is not None:
        elements.append(Paragraph("OFFICIAL ADJUSTER SETTLEMENT ADDENDUM", styles['Heading2']))
        
        # Determine AI Benchmark safely
        ai_benchmark = "N/A"
        if getattr(claim, "garage_audit_json", None):
            try:
                audit = json.loads(claim.garage_audit_json)
                ai_benchmark = f"Rs. {audit.get('ai_reconciled_cost', 0)}"
            except Exception:
                pass
        
        settlement_data = [
            ["Original Claimed", f"Rs. {claim.claim_amount}"],
            ["AI Benchmark", ai_benchmark],
            ["Final Authorized Settlement", f"Rs. {claim.final_approved_amount}"],
            ["Adjuster Notes", getattr(claim, "settlement_notes", "None provided")],
            ["Settlement Status", getattr(claim, "settlement_status", "pending").upper()]
        ]
        
        settlement_table = Table(settlement_data, colWidths=[200, 300])
        settlement_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
            # Highlight the final authorized row
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d4edda')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#155724')),
        ]))
        
        elements.append(settlement_table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Authorized By: Lead Adjuster (Digital Seal Applied)", styles['Normal']))
        elements.append(Spacer(1, 20))

    elements.append(Paragraph("Generated by AI Claims Validation System", styles['Normal']))

    doc.build(elements)
    return file_path