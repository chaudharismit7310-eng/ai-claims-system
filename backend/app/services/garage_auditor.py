import os
import json
import pdfplumber
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Schema Definition
class GarageItem(BaseModel):
    part_or_labor: str
    quoted_amount: float
    ai_benchmark_amount: float
    is_inflated: bool
    inflation_percentage: float

class GarageAuditResult(BaseModel):
    garage_name: Optional[str]
    total_quoted_cost: float
    ai_reconciled_cost: float
    total_inflation_amount: float
    inflation_percentage: float
    flagged_items: List[GarageItem]
    audit_verdict: str  # "FAIR", "MODERATELY_INFLATED", "GROSSLY_INFLATED"

def audit_garage_estimate(pdf_path: str, vehicle_make: str, ai_predicted_cost: float) -> dict:
    if not os.path.exists(pdf_path):
        return {}

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {}
    
    client = genai.Client(api_key=api_key)
    
    # Extract text from PDF
    pdf_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
        return {}

    prompt = f"""
    You are an expert AI Insurance Claims Auditor.
    I have provided the raw text from a Garage Estimate PDF for a {vehicle_make}.
    
    The AI Vision model estimated the total repair cost to be around ₹{ai_predicted_cost}.
    
    Extract all the line items (parts and labor) from this text and their quoted prices in INR (₹).
    For each line item, estimate a fair 'ai_benchmark_amount' based on standard OEM pricing for a {vehicle_make}.
    Calculate if it is inflated (quoted_amount > ai_benchmark_amount).
    Calculate the inflation_percentage.
    
    Calculate the total quoted cost from the document.
    Determine the total AI reconciled cost (sum of your benchmarks).
    Set the audit verdict to "FAIR" if inflation < 10%, "MODERATELY_INFLATED" if 10%-50%, and "GROSSLY_INFLATED" if > 50%.
    
    Raw PDF Text:
    {pdf_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GarageAuditResult,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"VLM Audit Error: {e}")
        return {}
