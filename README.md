# 🚗 AI-Powered Auto Insurance Claim Validation & Fraud Detection Platform

An enterprise-grade, end-to-end InsurTech platform that automates vehicle damage assessment, cross-validates policy metadata, detects visual & text discrepancies, and identifies fraud using multimodal Computer Vision (YOLOv8 + Gemini VLM), NLP, and Image Forensics.

---

## 🌟 Key Features

### 👁️ 1. Multimodal Computer Vision (YOLOv8 + Gemini VLM)
* **Visual Damage Detection:** Identifies severity, affected body components, and bounding boxes using YOLOv8.
* **Gemini VLM Analysis:** Performs multi-aspect multimodal inspection—evaluating vehicle damage severity, identifying car models, and performing camera authenticity/genuineness checks.
* **Heatmap Generation:** Overlays visual heatmap representations of detected damage zones onto vehicle photos.

### 🕵️‍♂️ 2. Advanced Image Forensics Engine
* **Digital Manipulation (ELA):** Runs Error Level Analysis to detect Photoshop alterations or digital tampering.
* **Image Hashing & Duplicate Matching:** Prevents resubmission of previously processed claim images across the database.
* **Metadata & EXIF Validation:** Flags missing EXIF timestamps or wiped metadata associated with internet downloads.
* **Stock/Web Photo Classification:** Identifies recycled or internet-sourced accident photos.

### 🧩 3. Directional Text-Visual Consistency Checker
* **Incident Description NLP:** Extracts directional collision context (e.g., *front, rear/back, side, roof, glass*).
* **Contradiction Detection:** Cross-checks natural language descriptions against visual damage findings (e.g., flags claims reporting a rear-end collision when photos show front bumper destruction).

### 💳 4. Vehicle Identity & Policy Cross-Validation
* **Automatic OCR License Plate Extraction:** Compares photo plates against registered policy records.
* **Vehicle Model Validation:** Ensures the registered car model matches both form inputs and visual VLM detections.
* **Active Claim Collisions:** Prevents duplicate active claims on the same vehicle.

### 📊 5. Explainable AI (XAI) & LLM Executive Summary
* **Additive Fraud Score Model:** Calculates a unified 0.0–1.0 risk score with explicit factor attribution.
* **LLM Executive Summary:** Generates clear, non-contradictory summaries and recommendations for insurance adjusters (*Approve*, *Investigate*, *Reject*).

---

## 🏗️ Architecture & Tech Stack

* **Backend:** Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL, Pydantic, PyTorch, OpenCV
* **AI & ML Models:** 
  * **YOLOv8** (Object & Damage Detection)
  * **Google Gemini 2.5 VLM** (Multimodal Visual & Text Reasoning)
  * **OpenCV / PIL** (ELA & Image Forensics)
* **Frontend:** React.js, Tailwind CSS / Vite (`frontend2`)
* **Auth & Security:** JWT (JSON Web Tokens) with HTTPBearer authentication

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
* Python 3.10+
* Node.js 18+
* Gemini API Key

---

### 1️⃣ Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env