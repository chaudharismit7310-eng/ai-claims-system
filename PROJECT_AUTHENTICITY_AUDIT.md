# Comprehensive Technical Authenticity & AI/ML Audit Report
**Project Title**: AI-Powered Auto Insurance Claim Validation & Fraud Detection Platform  
**Auditor**: Senior Software Engineer, AI/ML Auditor & Senior College Project Evaluator  
**Audit Date**: September 15, 2026  
**Workspace Root**: `c:\Users\Dell\ai-claims-system`  

---

## Executive Summary

This technical audit was conducted to verify whether the AI Claims Validation System is genuinely implemented and operational, or whether it relies on simulations, hardcoded outputs, fake inference, or disconnected workflows. The evaluation involved a complete static codebase review across backend services, database schemas, frontend applications, and AI/ML weights, alongside **live dynamic runtime execution tests** using the project's Python virtual environment (`Python 3.13.13`), PyTorch, Ultralytics, Google GenAI SDK, and the PostgreSQL database.

### Overall Authenticity Score: **66 / 100**

The project possesses **substantial genuine engineering**, including a custom 10-class YOLOv8 damage detection model (`models/car_damage_model.pt`), a live Google Gemini 2.5 Flash VLM integration with structured schema parsing, an EasyOCR license plate reader, real Error Level Analysis (ELA), zero-shot CLIP forgery detection (`openai/clip-vit-base-patch32`), OpenCV damage heatmaps, ReportLab PDF generation, and an active React + Vite frontend (`frontend2`).

However, **serious authenticity compromises, hardcoded shortcuts, and architectural flaws** prevent this project from functioning as a true end-to-end ML platform:
1. **Cost Estimation Model Disconnect**: The deployed GradientBoosting model (`cost_model.pkl`) only ever produces **three fixed numbers** (₹267,722.17, ₹132,641.51, ₹51,276.74) because `claim_routes.py` never passes vehicle make, age, or condition, and `cost_estimation.py` hardcodes damage severity to three discrete tiers.
2. **Fraud Model Synthetic Inflation & Swapped Features**: `train_combined_fraud.py` duplicates 1,000 Kaggle rows 15 times to claim a "15,000-sample dataset" (causing massive train/test data leakage), injects random synthetic noise for vision features, and does not even match the 17-feature deployed model (`fraud_model.pkl`). In production, 14 of the 17 inputs are hardcoded dummy defaults, two features are fed into swapped positions, and manual additive penalties (+15%, +20%, +34%, +35%) completely override the model's actual output.
3. **Hypersensitive EXIF Flagging**: Uploading any image without EXIF metadata (standard for WhatsApp, web browsers, and PNGs) triggers an automatic cascade that flags the claim as fraudulent, forces data consistency to `HIGHLY_INCONSISTENT`, and drives the fraud score to 1.0 (100% fraud).
4. **spaCy NLP & Perceptual Hashing Misrepresentation**: `nlp_analysis.py` and `consistency_checker.py` load spaCy but never use it, relying solely on Python substring searches (`in description_lower`). Image hashing uses raw MD5 byte hashing rather than perceptual hashing (pHash).
5. **Configuration & Dependency Breakdown**: `requirements.txt` is missing from the repository, and `database.py` contains a hardcoded PostgreSQL connection string (`postgresql://postgres:smit0605@localhost:5432/claims_db`) despite the README claiming the system runs on SQLite.

---

## 1. Feature Authenticity Verification Matrix

| Feature | Claimed Functionality | Actual Implementation | Evidence | Status | Required Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOv8 Damage Detection** | Custom model trained on 18k images (URFU + Curacel) across 10 damage classes (mAP50: 59.4%). | Real custom YOLOv8 model (`car_damage_model.pt`, 22.5MB). Detects 10 classes (`dent`, `scratch`, `crack`, `broken_glass`, `broken_part`, `paint_damage`, `headlight_damage`, `taillight_damage`, `bumper_damage`, `corrosion`). Generates real bounding boxes and confidences. | `backend/app/ai_models/yolov8_model.py:6-69`<br>`models/car_damage_model.pt`<br>Verified live inference: detected `bumper_damage` (conf: 0.268) and `broken_part` (conf: 0.268). | **VERIFIED** | Model and inference are authentic. Training data and training scripts should be archived in the repo for verification. |
| **Damage Heatmap Generation** | Visual heatmap overlays highlighting damage locations on vehicles. | Genuine OpenCV implementation using Jet colormap blended with original image (`cv2.addWeighted`), drawing bounding boxes and labels. | `backend/app/services/heatmap_generator.py:6-100`<br>Saves generated files to `backend/uploads/heatmaps/`. | **VERIFIED** | None. Works dynamically with real OpenCV code. |
| **Gemini 2.5 Flash VLM Multimodal Analysis** | Visual damage evaluation, severity grading, license plate extraction, and Indian cost range estimation via Google Gemini. | Authentic live integration using Google GenAI SDK (`gemini-2.5-flash`) and Pydantic structured output (`VLMAnalysisSchema`). | `backend/app/services/vlm_service.py:18-150`<br>Live test extracted plate `TN-01-AM-6142`, classified severity as `severe`, and detailed frontal damage. | **VERIFIED** | Move API key to secure environment configuration rather than committing in `.env`. |
| **LLM Executive Summary** | Natural language appraisal and final decision recommendation for adjusters. | Genuine Gemini 2.5 Flash call synthesizing claim data, fraud score, and forensic flags into an executive summary. | `backend/app/services/vlm_service.py:155-207`<br>Live execution generated 3-sentence appraisal ending with bolded **Reject** / **Approve**. | **VERIFIED** | None. Authentic GenAI feature. |
| **EasyOCR License Plate Recognition** | Automatic license plate extraction from vehicle photos. | Genuine EasyOCR reader with regex pattern `[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}`. Fails on complex angles, but has fallback to Gemini VLM. | `backend/app/services/ocr_service.py:12-33`<br>`backend/app/routes/claim_routes.py:168-175`<br>Live test extracted `T60+-AM6142` (conf 0.15); fell back to VLM which extracted `TN-01-AM-6142`. | **VERIFIED** | Improve OCR preprocessing (deskew, bilateral filter) to boost raw OCR accuracy before regex matching. |
| **Image ELA Forensics** | Error Level Analysis to detect Photoshop alterations or digital tampering. | Real PIL and NumPy implementation. Saves image at 90% JPEG quality, computes pixel difference, enhances brightness, and calculates mean difference score. | `backend/app/services/image_forensics.py:22-72`<br>Live execution produced authentic dynamic scores (e.g. `0.0547`). | **VERIFIED** | Adjust threshold sensitivity; normal compression artifacts can trigger false positive tampering flags. |
| **AI Image Forgery (CLIP)** | Detects AI-generated, stock, or manipulated images using CLIP zero-shot classification. | Genuine PyTorch + Hugging Face Transformers implementation using `openai/clip-vit-base-patch32` with 6 zero-shot prompts. | `backend/app/services/ai_forgery_detection.py:11-134`<br>Model loaded dynamically and computed real softmax probability distributions. | **VERIFIED** | Model weight download (~600MB) can delay first inference if offline. Cache weights locally. |
| **Duplicate Image Detection** | Perceptual image hashing to detect duplicate re-submissions. | Uses standard binary MD5 hashing (`hashlib.md5`), NOT perceptual hashing. Fails if image is re-saved, resized, or metadata changes by 1 byte. | `backend/app/services/image_forensics.py:8-20`<br>`backend/app/routes/claim_routes.py:140-145` | **PARTIALLY VERIFIED** / **MISLABELED** | Replace `hashlib.md5` with genuine perceptual hashing (`imagehash.phash` or `imagehash.dhash`). |
| **EXIF Metadata Validation** | Validates capture timestamps, camera models, and flags internet stock downloads. | Extracts EXIF via PIL. However, if EXIF is absent (as is typical for WhatsApp, web uploads, and PNGs), it aggressively marks `fraud_flag = True`, leading to a cascade that flags the entire claim as fraud. | `backend/app/utils/exif_extractor.py:6-65`<br>`backend/app/routes/claim_routes.py:186-207` | **PARTIALLY VERIFIED** / **HIGH DEFECT** | Treat missing EXIF as "inconclusive" rather than "positive fraud (+15% score)". |
| **ML Repair Cost Estimator** | Gradient Boosting Regressor trained on 150k Craigslist cars (R²=0.9395) with Indian localization. | Real `GradientBoostingRegressor` model exists in `cost_model.pkl`. However, `claim_routes.py` DOES NOT pass car model, age, or condition. Only 3 hardcoded damage severities (0.85, 0.60, 0.30) are ever passed. The model only ever predicts **₹267,722.17**, **₹132,641.51**, or **₹51,276.74**. | `backend/app/services/cost_estimation.py:61-75`<br>`backend/app/routes/claim_routes.py:314-319`<br>Live execution confirmed the model only outputs these 3 values across all possible claims. | **SIMULATED** / **DISCONNECTED** | Connect user inputs (`car_model`, `vehicle_age`, `claim_amount`, part damage count) to the model feature array in `claim_routes.py`. |
| **RandomForest Fraud Detection Model** | Trained on 16,420 records with SMOTE, AUC=0.9627 across 17 features. | Real `RandomForestClassifier` exists in `fraud_model.pkl`. However, 14 of 17 features are hardcoded defaults (`driver_age=35`, `vehicle_age=5`, `deductible=1000`, etc.). The training script `train_combined_fraud.py` does not match the deployed model (trains 10 features, duplicates 1,000 rows 15x with synthetic noise). Model output is overridden by manual additive rules. | `backend/app/services/fraud_detection.py:50-71`<br>`backend/app/routes/claim_routes.py:193-207`<br>`backend/train_combined_fraud.py:20-53` | **HARDCODED** / **SIMULATED** | Train a unified model on real tabular + vision features. Pass real registered user/vehicle data into all 17 feature slots. |
| **Directional Consistency Checker** | spaCy NLP engine extracts collision direction entities from text and cross-checks with vision. | spaCy is imported and loaded into memory, but **NEVER USED**. Logic uses simple Python substring matching (`any(k in description_lower)`). However, the directional contradiction logic itself works. | `backend/app/services/consistency_checker.py:59-98`<br>`backend/app/services/nlp_analysis.py:8-16` | **PARTIALLY VERIFIED** / **MISLABELED** | Implement real spaCy entity recognition or dependency matcher, or correct documentation to reflect keyword matching. |
| **Explainable AI (XAI)** | XAI engine attributing risk percentages to individual factors. | Does NOT use SHAP, LIME, or tree interpretability. Uses static hardcoded percentage contributions (`+40%` for duplicate, `+35%` for AI detected, `+15%` for EXIF, etc.) inside an `if/else` block. | `backend/app/services/explainable_ai.py:19-106` | **HARDCODED** / **RULE-BASED** | Replace hardcoded attribution with SHAP (`shap.TreeExplainer`) on the Random Forest fraud model. |
| **Decision Engine** | Suggests claim approval, rejection, or partial payout based on AI confidence. | Static 50-line rule-based script with hardcoded thresholds and hardcoded payout percentages (90% for opponent fault, 95% for natural, 50% for driver fault). | `backend/app/services/decision_engine.py:1-50` | **RULE-BASED** | Retain as policy rules, but do not misrepresent as an AI/ML model. |
| **PDF Claim Report Generation** | Automated generation of professional adjuster PDF reports. | Fully implemented using ReportLab `SimpleDocTemplate`, custom tables, color palettes, and claim metrics. | `backend/app/utils/pdf_generator.py:7-71`<br>`backend/app/routes/claim_routes.py:450-457`<br>Live test downloaded valid 3,112-byte PDF for Claim #52. | **VERIFIED** | None. Clean implementation. |
| **Authentication & RBAC** | JWT-based auth with bcrypt password hashing and customer/agent/admin roles. | Fully implemented using `python-jose` and `passlib.bcrypt`. Protects endpoints via `HTTPBearer` dependencies and enforces role checks. | `backend/app/auth.py:1-35`<br>`backend/app/routes/auth_routes.py`<br>`backend/app/routes/admin_routes.py:14-22` | **VERIFIED** | Ensure JWT secret key is securely generated in production. |
| **Active Claim & Policy Expiry Validation** | Prevents multiple active claims for the same vehicle and blocks claims on expired policies. | Fully implemented and enforced in both frontend (`SubmitClaim.jsx`) and backend (`claim_routes.py`). | `backend/app/routes/claim_routes.py:104-121`<br>`frontend2/src/SubmitClaim.jsx:71-74`<br>Live test verified rejection of duplicate active claim on vehicle `TN-01-AM-6142` with HTTP 400. | **VERIFIED** | None. Robust validation logic. |
| **Customer & Agent Dashboards** | Full frontend UI for submitting claims, tracking claims, verifying vehicles, and reviewing claims. | React 19 + Vite application (`frontend2`) with TailwindCSS, Axios interceptors, voice input, and Recharts analytics. Builds cleanly (`npm run build` passed with 0 errors). | `frontend2/src/App.jsx`<br>`frontend2/src/SubmitClaim.jsx`<br>`frontend2/src/AgentDashboard.jsx`<br>`frontend2/src/AdminPanel.jsx` | **VERIFIED** | None. High-quality UI connected to real backend APIs. |
| **Email Notification Service** | Sends automated email notifications on claim submission and agent review. | `email_service.py` contains SMTP functions, but `send_claim_submitted` and `send_claim_decision` are **NEVER called** anywhere in the backend routes. `EMAIL_USER` and `EMAIL_PASS` are absent from `.env`. | `backend/app/services/email_service.py:1-79`<br>`backend/app/routes/claim_routes.py` (no email imports) | **NOT IMPLEMENTED** | Wire `send_claim_submitted` and `send_claim_decision` into `claim_routes.py` and configure SMTP credentials. |
| **Unused Service: `image_processing.py`** | Claimed image preprocessing utility. | Empty file (0 bytes). | `backend/app/services/image_processing.py` | **NOT IMPLEMENTED** | Implement image resizing/normalization utilities or delete the empty file. |
| **Dead Code: `damage_detection.py`** | Damage detection service with hardcoded fallback bounding boxes. | Contains hardcoded dummy detections (`{"label": "scratch", "bbox": [120, 200, 350, 420]}`), but is **completely unused** because `claim_routes.py` imports `backend/app/ai_models/yolov8_model.py` instead. | `backend/app/services/damage_detection.py:74-84` | **SIMULATED (DEAD CODE)** | Remove the obsolete file to avoid confusion during code review. |

---

## 2. Detailed Technical Audit Findings & Issues

### Issue 1: Cost Estimation ML Predicts Only 3 Fixed Discrete Values
- **File Path**: [backend/app/services/cost_estimation.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/cost_estimation.py#L61-L75), [backend/app/routes/claim_routes.py](file:///c:/Users/Dell/ai-claims-system/backend/app/routes/claim_routes.py#L314-L319)
- **Severity**: **CRITICAL**
- **Explanation**:  
  The project documentation claims a Gradient Boosting Regressor trained on 149,987 records predicts dynamic vehicle repair costs with an $R^2$ score of 0.9395. A real model does exist in `cost_model.pkl` expecting 7 features: `['vehicle_age', 'condition_num', 'make_encoded', 'type_encoded', 'car_value_inr', 'damage_severity', 'odometer']`.  
  However, in `claim_routes.py`:
  ```python
  cost_result = estimate_repair_cost(
      damage_confidence=damage_conf,
      claim_amount=claim_amount,
      driver_fault=driver_fault,
      fraud_score=fraud_score
  )
  ```
  `vehicle_make`, `vehicle_age`, and `vehicle_condition` are **never passed**. Inside `cost_estimation.py`:
  - `make_encoded` is hardcoded to `0`
  - `type_encoded` is hardcoded to `0`
  - `odometer` is hardcoded to `50000`
  - `car_value_inr` defaults to `800000`
  - `damage_severity` is hardcoded to only 3 values: `0.85` if confidence > 0.7, `0.60` if confidence > 0.4, and `0.30` otherwise.  
  
  **Runtime Execution Proof**:  
  When evaluated across all inputs, the model produces only 3 numbers:
  - **₹267,722.17** (for any severe damage)
  - **₹132,641.51** (for any moderate damage)
  - **₹51,276.74** (for any minor damage)  
  A ₹15,000 claim on an old Maruti Alto and a ₹1,500,000 claim on a new BMW receive the exact same predicted repair cost if the YOLO confidence falls into the same bucket.
- **Recommended Fix**:  
  Extract the actual vehicle brand from `car_model` or registered vehicle profile, map the brand using `model_data['le_make']`, compute `vehicle_age = current_year - registration_year`, and calculate `damage_severity` as a continuous ratio of detected damaged parts over total vehicle panels. Pass all 7 real features to `cost_model.predict()`.

---

### Issue 2: Fraud Detection Pipeline Uses Hardcoded Defaults, Swapped Features & Synthetic Training
- **File Path**: [backend/app/services/fraud_detection.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/fraud_detection.py#L50-L68), [backend/train_combined_fraud.py](file:///c:/Users/Dell/ai-claims-system/backend/train_combined_fraud.py#L20-L53), [backend/app/routes/claim_routes.py](file:///c:/Users/Dell/ai-claims-system/backend/app/routes/claim_routes.py#L193-L207)
- **Severity**: **CRITICAL**
- **Explanation**:  
  The documentation claims a 17-feature Random Forest classifier trained on 16,420 real records using SMOTE.  
  1. **Training Discrepancy & Fake Scale**: `train_combined_fraud.py` takes a 1,000-row Kaggle CSV, replicates it 15 times (`[df_tabular] * multiplier`), and splits train/test on duplicated rows. This creates massive data leakage (the exact same rows exist in both train and test sets), producing artificially high metrics. Furthermore, `train_combined_fraud.py` trains a 10-feature model, but the deployed model in `fraud_model.pkl` has 17 features, proving that `train_combined_fraud.py` was not even used to train the deployed model.
  2. **14 Hardcoded Default Features in Production**: When `detect_fraud()` is called from `claim_routes.py`, no customer profile kwargs are provided. The model receives static defaults: `driver_age=35`, `vehicle_age=5`, `deductible=1000`, `past_claims=0`, `police_report=0`, `witness_present=0`, `supplements=1`, `address_change=0`, `number_of_cars=1`.
  3. **Swapped Feature Vector**: In `fraud_model.pkl`, feature index 14 is `BasePolicy`, 15 is `AccidentArea`, and 16 is `PolicyType`. In `fraud_detection.py`, index 14 is assigned to `AccidentArea`, 15 to `PolicyType`, and 16 to `BasePolicy`. The model is evaluating input features in the wrong columns.
  4. **Output Overwritten by Manual Additive Heuristics**: In `claim_routes.py`, the ML model's output probability is immediately overshadowed by manual additive constants (+0.15 for missing EXIF, +0.20 for internet override, +0.35 for vehicle mismatch, +0.34 for consistency score), rendering the actual Random Forest inference inconsequential.
- **Recommended Fix**:  
  Align the feature order with `fraud_model.feature_names_in_`. Pull real policyholder age, past claims count, and deductible from the database `Policy` and `Vehicle` tables. Feed continuous damage severity from YOLO and VLM into the model rather than adding static constants to the output.

---

### Issue 3: Missing EXIF Metadata Cascades Into Automatic 100% Fraud
- **File Path**: [backend/app/utils/exif_extractor.py](file:///c:/Users/Dell/ai-claims-system/backend/app/utils/exif_extractor.py#L10-L18), [backend/app/routes/claim_routes.py](file:///c:/Users/Dell/ai-claims-system/backend/app/routes/claim_routes.py#L186-L280)
- **Severity**: **HIGH**
- **Explanation**:  
  In `exif_extractor.py`:
  ```python
  if not exif_data:
      return {"has_exif": False, "fraud_flag": True, "fraud_reason": "No EXIF metadata found - image may be edited"}
  ```
  Virtually all photos uploaded through web forms, mobile web browsers, or sent via WhatsApp/messaging platforms have EXIF metadata automatically stripped.  
  Because `fraud_flag` is set to `True`:
  1. `claim_routes.py` marks `is_internet_download = True`.
  2. `final_vlm_is_genuine` is forced to `False` (even when Gemini VLM determines the photo is completely genuine).
  3. `fraud_score` receives an immediate +0.20 penalty.
  4. Synergy enforcement forces `consistency_result["overall_status"] = "HIGHLY_INCONSISTENT"` and cuts the consistency score to `0.15`.
  5. An additional `(1.0 - 0.15) * 0.40 = +0.34` fraud penalty is added.
  
  **Runtime Execution Proof**:  
  In the database, claims #51, #52, #53, #54, and #55 all received fraud scores of 0.96 to 1.0 because regular images lacked EXIF tags.
- **Recommended Fix**:  
  Distinguish between "missing EXIF" (common in normal digital transfers) and "tampered EXIF" (conflicting dates/GPS). Missing EXIF should be marked as neutral (`fraud_flag=False`, `fraud_score_addition=0.0`). Only flag fraud if EXIF timestamps contradict the claim incident date or if software tags indicate Photoshop/GIMP.

---

### Issue 4: `requirements.txt` Missing From Repository
- **File Path**: `backend/requirements.txt` (Non-existent)
- **Severity**: **HIGH**
- **Explanation**:  
  `README.md` lines 151 and 185 state that dependencies must be installed using:
  ```bash
  pip install -r requirements.txt
  ```
  Attempting to run this command fails with `FileNotFoundError`. Any external evaluator attempting to install the project from scratch according to the documentation will be unable to set up the environment.
- **Recommended Fix**:  
  Generate an exact `requirements.txt` from the working virtual environment using `pip freeze > backend/requirements.txt`.

---

### Issue 5: Hardcoded Database Connection String & Documentation Discrepancy
- **File Path**: [backend/app/database.py](file:///c:/Users/Dell/ai-claims-system/backend/app/database.py#L5-L7), [README.md](file:///c:/Users/Dell/ai-claims-system/README.md#L117)
- **Severity**: **HIGH**
- **Explanation**:  
  `README.md` lists `Database: SQLite`. However, `backend/app/database.py` contains:
  ```python
  DATABASE_URL = "postgresql://postgres:smit0605@localhost:5432/claims_db"
  engine = create_engine(DATABASE_URL)
  ```
  The connection string is hardcoded directly in Python code and ignores `settings.DATABASE_URL` from `config.py`. If a evaluator runs the project on a machine without a local PostgreSQL instance listening on port 5432 with password `smit0605`, the backend fails immediately upon launch.
- **Recommended Fix**:  
  Change `database.py` to use `from app.config import settings; engine = create_engine(settings.DATABASE_URL)`. Provide a fallback to SQLite (`sqlite:///./claims.db`) so evaluators can run the project without configuring PostgreSQL.

---

### Issue 6: Misrepresentation of spaCy NLP & Directional Extraction
- **File Path**: [backend/app/services/nlp_analysis.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/nlp_analysis.py#L8-L16), [backend/app/services/consistency_checker.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/consistency_checker.py#L59-L98)
- **Severity**: **MEDIUM**
- **Explanation**:  
  The documentation asserts: *"spaCy NLP Engine: Extracts collision direction entities from user narrative descriptions."*  
  In reality:
  - `nlp_analysis.py` defines `load_nlp()` which loads `en_core_web_sm`, but `nlp` is **never called**. It only performs `sum(1 for kw in driver_keywords if kw in text_lower)`.
  - `consistency_checker.py` uses plain Python list membership (`any(k in description_lower for k in ["front", "bonnet", ...])`).  
  While the directional contradiction detection successfully identifies conflicting claims (e.g. rear narrative vs front image damage), it is achieved via basic substring matching, not spaCy entity extraction or linguistic dependency parsing.
- **Recommended Fix**:  
  Either integrate spaCy's `Matcher` or `EntityRuler` to extract syntactic relationships (e.g. `[ROOT: hit] -> [obl: rear]`), or update the project documentation to state that directional validation is keyword-based.

---

### Issue 7: Explainable AI (XAI) is Hardcoded Rule Weights, Not Model Interpretability
- **File Path**: [backend/app/services/explainable_ai.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/explainable_ai.py#L19-L106)
- **Severity**: **MEDIUM**
- **Explanation**:  
  The documentation claims an "Explainable AI (XAI) & Decision Engine". Standard AI/ML XAI relies on game-theoretic attribution (SHAP values), local surrogate models (LIME), or integrated gradients.  
  The code in `explainable_ai.py` is a manual list of hardcoded `if` statements:
  ```python
  if "DUPLICATE" in image_fraud_reason:
      factors.append({"factor": "Duplicate Image Detected", "contribution": 0.40, ...})
  if "AI DETECTED" in image_fraud_reason:
      factors.append({"factor": "AI Forgery Detection", "contribution": 0.35, ...})
  ```
- **Recommended Fix**:  
  Implement `shap.TreeExplainer` on the Random Forest fraud classifier to display true feature importance bars (e.g. impact of claim amount, driver age, vehicle age) alongside business rule alerts.

---

### Issue 8: Duplicate Image Detection Uses MD5 Hashing Instead of Perceptual Hashing
- **File Path**: [backend/app/services/image_forensics.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/image_forensics.py#L8-L20)
- **Severity**: **LOW**
- **Explanation**:  
  The README claims *"Perceptual Image Hashing: Detects duplicate image re-submissions across past claim records."*  
  The function `get_image_hash()` executes `hashlib.md5(f.read()).hexdigest()`. MD5 is a cryptographic byte hash. If an applicant crops 1 pixel, adjusts contrast slightly, or re-saves the JPEG with 99% quality, the MD5 hash changes completely, bypassing duplicate detection.
- **Recommended Fix**:  
  Install `imagehash` and compute `str(imagehash.phash(Image.open(image_path)))`. Store the Hamming distance query in the database to detect visually identical images regardless of format or compression differences.

---

### Issue 9: Disconnected Email Notification Service & Empty Preprocessing File
- **File Path**: [backend/app/services/email_service.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/email_service.py), [backend/app/services/image_processing.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/image_processing.py)
- **Severity**: **LOW**
- **Explanation**:  
  `image_processing.py` is an empty 0-byte file. `email_service.py` defines functions for claim notifications, but they are never called in `claim_routes.py`.
- **Recommended Fix**:  
  Remove `image_processing.py` or implement genuine image normalization logic. Wire `send_claim_submitted` into `submit_claim` and `send_claim_decision` into `agent_review`.

---

## 3. Final Evaluator Verdict

### 1. Overall Authenticity Score: 66 / 100
**Calculation Breakdown**:
- **Core AI/ML Models & Real Inference**: **15 / 30** (Custom YOLOv8 is real and functional; fraud and cost models are undermined by hardcoded inputs, feature swapping, and fixed 3-value output quantization).
- **Multimodal VLM, Vision & Forensics**: **23 / 25** (Gemini 2.5 Flash, EasyOCR, ELA, and CLIP zero-shot forgery detection are authentic and operational).
- **Backend Architecture, API & Database**: **12 / 20** (Clean FastAPI architecture, role-based auth, and dynamic queries; penalized for missing `requirements.txt` and hardcoded PostgreSQL connection).
- **NLP, Consistency & Decision Engine**: **7 / 15** (Directional checks function dynamically, but rely on string matching; spaCy is unused; XAI is static rule weights).
- **Frontend & End-to-End Integration**: **9 / 10** (Vite + React frontend builds cleanly, is connected to real API endpoints, and handles state and data visualization dynamically).

### 2. Features That Genuinely Work
1. **Custom YOLOv8 Vehicle Damage Detection**: Executes real inference, detecting specific damage classes (`bumper_damage`, `broken_part`, etc.) with real bounding box coordinates.
2. **Google Gemini 2.5 Flash VLM Integration**: Live multimodal damage inspection, plate recognition fallback, and executive summary generation.
3. **EasyOCR License Plate Recognition**: Successfully reads text from images with regex validation and fallback to VLM.
4. **Error Level Analysis (ELA)**: Computes authentic compression artifact disparity via PIL/NumPy.
5. **AI Forgery Detection (CLIP)**: Genuine zero-shot classification using `openai/clip-vit-base-patch32`.
6. **OpenCV Damage Heatmap Overlay**: Generates genuine jet colormap heatmaps with bounding boxes and legends.
7. **ReportLab PDF Generation**: Automatically generates downloadable adjuster PDF summaries.
8. **Authentication & Role-Based Access**: Secure JWT auth with password hashing and role validation (customer, agent, admin).
9. **Active Claim & Expired Policy Guardrails**: Successfully prevents duplicate active submissions and rejects expired policies.
10. **Frontend Application**: Multi-role dashboards (Customer, Agent, Admin, Analytics with Recharts) rendered dynamically.

### 3. Hardcoded or Simulated Features
1. **Repair Cost Prediction Output**: Quantized into exactly 3 fixed values (₹267k, ₹132k, ₹51k) because input features are disconnected.
2. **Fraud Detection Input Vector**: 14 out of 17 features are hardcoded defaults; inputs are swapped; output probability is overridden by static rule additions.
3. **Explainable AI (XAI)**: Static hardcoded percentages (+40%, +35%, +15%) rather than ML attribution (SHAP/LIME).
4. **Decision Engine**: Hardcoded `if/else` rules with fixed confidence numbers (0.90, 0.88, 0.70, 0.50).
5. **Image Hashing**: Plain MD5 byte hashing instead of the claimed perceptual hashing (pHash).

### 4. Features That Could Not Be Verified
1. **Original Model Training Datasets**: `data/datasets/` is empty; original training logs, notebooks, and dataset splits for the 18k YOLO damage images and 150k Craigslist cars are missing.
2. **Reported Accuracy Claims**: Metrics like "Headlight Damage: 93.8%", "RandomForest: AUC = 0.9627", and "Gradient Boosting: R² = 0.9395" could not be independently computed from raw validation splits because validation sets are not packaged in the repository.

### 5. Critical Bugs That Could Expose the Project During Viva
1. **Cost Predictor Invariance**: If an examiner asks to submit two claims for two different cars (e.g. a ₹15,000 claim on an Alto vs a ₹300,000 claim on a Mercedes), the AI will output the **exact same estimated cost** for both if they have the same YOLO confidence level.
2. **Missing EXIF False Positive Cascade**: Uploading any screenshot or WhatsApp photo causes the claim to be flagged as 100% fraud and "HIGHLY INCONSISTENT" due to the strict `if not exif_data` check.
3. **Database Dependency Crash on Other Machines**: If the examiner clones the repo and starts it without PostgreSQL configured with password `smit0605`, the backend crashes on line 5 of `database.py`.

### 6. Missing Implementations
1. `backend/requirements.txt` (Missing dependency manifest).
2. True perceptual image hashing (pHash/dHash).
3. spaCy linguistic entity extraction (spaCy is loaded but unused).
4. Automated email dispatch on claim submission / approval.

### 7. Readiness for College Demonstration and Viva
**Current Status**: **CONDITIONAL PASS / RISKY FOR LIVE DEMO**  
The project visually looks outstanding and several complex components (YOLO, Gemini VLM, CLIP, OpenCV, React, PDF generation) genuinely function. However, an astute evaluator who inspects `cost_estimation.py`, `train_combined_fraud.py`, or tests claims with different car models will immediately detect the hardcoded inputs and fixed-value cost predictions.

### 8. Top 5 Changes Required Before Final Submission
1. **Connect Real Vehicle Data to Cost & Fraud Models**:  
   Modify [backend/app/routes/claim_routes.py](file:///c:/Users/Dell/ai-claims-system/backend/app/routes/claim_routes.py#L314) to extract real vehicle make, vehicle age, and damage severity, and pass them into `estimate_repair_cost()` and `detect_fraud()`. Eliminate the hardcoded 3-tier severity mapping in `cost_estimation.py`.
2. **Fix EXIF Metadata Sensitivity**:  
   In [backend/app/utils/exif_extractor.py](file:///c:/Users/Dell/ai-claims-system/backend/app/utils/exif_extractor.py#L14), do not mark `fraud_flag = True` solely because EXIF tags are missing. Treat missing EXIF as neutral so genuine user photos are not penalized.
3. **Generate `requirements.txt` & Enable SQLite Fallback**:  
   Run `pip freeze > backend/requirements.txt` and update [backend/app/database.py](file:///c:/Users/Dell/ai-claims-system/backend/app/database.py#L5) to fall back to `sqlite:///./claims.db` if PostgreSQL is unreachable.
4. **Fix Swapped Feature Order in Fraud Vector**:  
   In [backend/app/services/fraud_detection.py](file:///c:/Users/Dell/ai-claims-system/backend/app/services/fraud_detection.py#L50-L68), reorder the feature vector so `BasePolicy`, `AccidentArea`, and `PolicyType` match the exact order in `fraud_model.feature_names_in_`.
5. **Align Project Documentation with Actual Implementation**:  
   Clarify in `README.md` that directional validation uses keyword matching and that image hashing uses MD5, or upgrade those modules to genuine spaCy dependency matching and perceptual image hashing (`imagehash.phash`).
