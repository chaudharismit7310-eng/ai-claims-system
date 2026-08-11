#  AI-Powered Auto Insurance Claim Validation & Fraud Detection Platform

An enterprise-grade, end-to-end InsurTech platform that automates vehicle damage assessment, cross-validates policy metadata, detects visual & text discrepancies, estimates repair costs, and identifies fraud using multimodal Computer Vision (YOLOv8 + Gemini VLM), Machine Learning (RandomForest + Gradient Boosting), NLP, and Image Forensics.

---

##  System Architecture

```text
Customer Submits Claim
         │
         ▼
Frontend (React + Vite) ──[frontend2]
         │
         ▼
Backend API (FastAPI)
         │
┌────────────────────────────────────────────────────────┐
│                      AI Pipeline                       │
│                                                        │
│  1. YOLOv8 Damage Detection (Custom Trained 18k Imgs)  │
│  2. Gemini VLM Multimodal Analysis                     │
│  3. Image Forensics (ELA Tampering & Hash Match)       │
│  4. EasyOCR License Plate Extraction                   │
│  5. NLP Fault Analysis (spaCy Directional Checker)     │
│  6. Fraud Detection ML (RandomForest - 96.27% AUC)     │
│  7. Cost Estimation ML (Gradient Boosting - 93.95% R²) │
│  8. Decision Engine & Explainable AI (XAI)             │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
                 Agent Dashboard Review
                           │
                           ▼
               Claim Approved / Rejected
 Key Features & Custom ML Models
 1. YOLOv8 Car Damage Detection
Datasets Trained On: URFU + Curacel AI Datasets (17,984 total images across 10 merged damage classes).

Training Setup: Trained on Kaggle Notebooks using Dual Tesla T4 GPUs (DDP) for 100 Epochs.

Key Class Accuracies (mAP50):

Headlight Damage: 93.8%

Broken Glass: 93.4%

Bumper Damage: 91.2%

Taillight Damage: 89.6%

Overall mAP50: 59.4%

Outputs: Bounding box coordinates, confidence scores, and visual heatmap overlays.

 2. Multi-Feature Fraud Detection ML Model
Datasets Trained On: Kaggle Vehicle Claim Fraud + Auto Insurance Claims (16,420 real records).

Class Imbalance Handling: Applied SMOTE (Synthetic Minority Over-sampling Technique) to expand 6% fraud cases into 150,000 balanced records.

Engineered Features (17 total): Age, Vehicle Price, Deductible, Driver Rating, Past Claims, Police Report Status, Witness Presence, Base Policy, etc.

Model Performance:

RandomForest (300 Trees): AUC = 0.9627 (96.27%) ➔ Deployed Model (35.2 MB)

XGBoost: AUC = 0.9755 (97.55%)

Ensemble: AUC = 0.9681 (96.81%)

 3. Machine Learning Repair Cost Estimator
Dataset Trained On: Craigslist Cars Dataset (149,987 cleaned records).

India Localization Engine:

USD to INR Conversion (×83) & Vehicle Age Calculation.

India OEM Base Valuation Mapping (Maruti: ₹6L, Hyundai: ₹8L, Honda: ₹9L, Tata: ₹7L, BMW: ₹40L).

Multi-Tier Damage Severity Multipliers (Minor: 5–15%, Moderate: 15–35%, Severe: 35–65%).

Model Performance:

Gradient Boosting Regressor: R² = 0.9395 (93.95%) | MAE = ₹43,223 ➔ Deployed Model (0.9 MB)

XGBoost Regressor: R² = 0.9378

RandomForest Regressor: R² = 0.9386

 4. Advanced Image Forensics Engine
Digital Manipulation (ELA): Runs Error Level Analysis to detect Photoshop alterations or digital tampering.

Perceptual Image Hashing: Detects duplicate image re-submissions across past claim records.

EXIF Metadata Validation: Flags wiped metadata, missing timestamps, or web-downloaded stock photos.

 5. Gemini VLM Multimodal Analysis
Contextual Reasoning: Evaluates vehicle damage severity, vehicle make/model alignment, and camera photo genuineness.

Executive Summaries: Generates natural language summaries and reasoning for insurance adjusters.

 6. Directional Text-Visual Consistency Checker
spaCy NLP Engine: Extracts collision direction entities from user narrative descriptions.

Contradiction Detection: Cross-checks natural language descriptions against visual damage findings (e.g., flags claims reporting a rear-end collision when photos show front bumper destruction).

 7. Explainable AI (XAI) & Decision Engine
Risk Score Attribution: Breaks down risk scores with explicit factor percentages (e.g., Duplicate Image: +40%, AI Forgery: +35%, Inconsistent Description: +26%).

Automated Output: Generates PDF reports and suggests final decisions (Approve, Manual Review, Reject).

 Tech Stack
Frontend: React, Vite, TailwindCSS

Backend: FastAPI, SQLAlchemy, Pydantic

Database: SQLite

AI/ML Models: YOLOv8s, RandomForest, GradientBoosting, XGBoost

Computer Vision & Forensics: OpenCV, ELA, Perceptual Hashing, EasyOCR

Multimodal VLM: Google Gemini 2.5 VLM

NLP: spaCy NER

Security & Auth: JWT (python-jose), bcrypt password hashing

PDF Generator: ReportLab

 Quickstart Guide
Prerequisites
Python 3.10+

Node.js 18+

 Backend Setup (FastAPI)
Bash
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

# Start FastAPI server
python -m uvicorn app.main:app --reload
API server running at http://127.0.0.1:8000

Interactive Docs (Swagger): http://127.0.0.1:8000/docs

 Frontend Setup (React - frontend2)
Open a new terminal window from project root:

Bash
# Navigate to active frontend directory
cd frontend2

# Install dependencies
npm install

# Start React development server
npm run dev
Web UI running at http://localhost:5173

 Repository Structure
Plaintext
ai-claims-system/
├── backend/
│   ├── app/
│   │   ├── ai_models/        # Deployed ML weights (fraud_model.pkl, cost_model.pkl)
│   │   ├── models/           # SQLAlchemy DB models
│   │   ├── routes/           # FastAPI endpoints (claims, auth, analytics, etc.)
│   │   ├── schemas/          # Pydantic data validation
│   │   └── services/         # VLM, Forensics, Consistency, NLP, Cost Engine
│   ├── reports/              # Auto-generated PDF claim reports
│   ├── main.py               # FastAPI entry point
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment variables (Gemini API key, JWT secret)
├── frontend2/                # Active React UI for Customers & Agents
├── models/                   # Custom YOLOv8 trained weights (car_damage_model.pt)
└── README.md
🔮 Production Roadmap & Future Scope
File Upload Middleware: Enforce file size limits (5MB) and strictly restrict mime types (.jpg, .png, .pdf).

API Rate Limiting: Implement slowapi / Redis rate limiting (100 req/min) to prevent brute-force attacks.

Token Persistence: Store JWT tokens in localStorage for persistent session management on page refresh.

Real-Time Video Inspection: Extend Gemini VLM to process video walkthroughs of damaged vehicles instead of static photos.

WhatsApp / SMS Notifications: Integration with Twilio/WhatsApp API for instant customer claim status updates.