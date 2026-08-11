import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Gmail SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("EMAIL_USER", "")
SMTP_PASS = os.getenv("EMAIL_PASS", "")

def send_email(to_email: str, subject: str, body: str):
    if not SMTP_USER or not SMTP_PASS:
        print(f"Email not configured - would send to {to_email}: {subject}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_claim_submitted(to_email: str, claim_id: int, customer_name: str):
    subject = f"Claim #{claim_id} Submitted Successfully"
    body = f"""
    <h2>Claim Submitted Successfully!</h2>
    <p>Dear {customer_name},</p>
    <p>Your claim <strong>#{claim_id}</strong> has been submitted and is under review.</p>
    <p>Our AI system is analyzing your claim. An agent will review it shortly.</p>
    <br>
    <p>AI Claims Validation System</p>
    """
    return send_email(to_email, subject, body)

def send_claim_decision(to_email: str, claim_id: int, 
                        customer_name: str, decision: str, 
                        approved_amount: float, agent_notes: str):
    subject = f"Claim #{claim_id} Decision: {decision.upper()}"
    color = "#27ae60" if decision == "approved" else "#e74c3c" if decision == "rejected" else "#f39c12"
    body = f"""
    <h2>Claim Decision Update</h2>
    <p>Dear {customer_name},</p>
    <p>Your claim <strong>#{claim_id}</strong> has been reviewed.</p>
    <p style="color:{color}; font-size:18px; font-weight:bold;">
        Decision: {decision.upper()}
    </p>
    <p>Approved Amount: <strong>₹{approved_amount:,.2f}</strong></p>
    <p>Agent Notes: {agent_notes or 'No notes'}</p>
    <br>
    <p>AI Claims Validation System</p>
    """
    return send_email(to_email, subject, body)

def send_vehicle_status(to_email: str, vehicle_number: str, 
                        status: str, agent_notes: str):
    subject = f"Vehicle {vehicle_number} Verification: {status.upper()}"
    color = "#27ae60" if status == "verified" else "#e74c3c"
    body = f"""
    <h2>Vehicle Verification Update</h2>
    <p>Your vehicle <strong>{vehicle_number}</strong> verification status:</p>
    <p style="color:{color}; font-size:18px; font-weight:bold;">
        {status.upper()}
    </p>
    <p>Notes: {agent_notes or 'No notes'}</p>
    <br>
    <p>AI Claims Validation System</p>
    """
    return send_email(to_email, subject, body)