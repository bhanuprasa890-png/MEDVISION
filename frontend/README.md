# MedVision AI — Frontend Web Application

## 1. Overview
The MedVision AI frontend is built with React, Vite, and Tailwind CSS. It is an exclusively presentation and client-side communication tier.

### Strict Boundary Rules:
- Contains only UI components, custom hooks, and HTTP API client services.
- Contains NO Python code, database connections, secret keys, or medical inference algorithms.

---

## 2. Directory Structure
```text
frontend/
├── public/                 # Static public assets (e.g., vite.svg)
├── src/
│   ├── assets/             # Branding icons & illustrations
│   ├── components/         # Reusable UI widgets:
│   │   ├── Header.jsx      # Navigation header & research prototype badge
│   │   ├── Footer.jsx      # Global medical disclaimer footer
│   │   ├── ImageUploader.jsx # Drag-and-drop file selector & format validator
│   │   ├── AnalysisResultCard.jsx # Generic placeholder inspection card
│   │   └── RetinaPredictionResultCard.jsx # Dedicated RetinaGuard 5-class DR card & Grad-CAM visualizer
│   ├── hooks/              # Custom hooks (useImageUpload)
│   ├── pages/              # Modality views:
│   │   ├── HomePage.jsx    # Architectural overview & navigation
│   │   ├── RetinaAnalysisPage.jsx # RetinaGuard fundus analysis & Grad-CAM viewer
│   │   └── ChestXrayAnalysisPage.jsx # CXR module (protected & untouched)
│   ├── services/           # API fetch client (api.js: predictRetina, getRetinaModelStatus)
│   ├── App.jsx             # Top-level shell and tab navigation
│   ├── main.jsx            # React root mount
│   └── index.css           # Tailwind base, components, utilities
├── index.html              # HTML5 entrypoint
├── package.json            # Node scripts & dependencies
├── vite.config.js          # Vite build & dev server config
└── tailwind.config.js      # Tailwind CSS design system tokens
```

---

## 3. RetinaGuard Frontend Integration (Step 5)

### Connected Endpoints:
- `POST /api/v1/retina/predict?include_gradcam=true`: Multipart file upload for ResNet-18 5-class Diabetic Retinopathy prediction and Grad-CAM explainability.
- `GET /api/v1/retina/model-status`: Real-time model readiness and device verification.

### Key Features:
- **Client-Side Validation**: Ensures file format (`.jpg`, `.jpeg`, `.png`, `.webp`) and file size limits (≤10 MB, >0 bytes) before submission.
- **Model Readiness Status**: Real-time badge indicating whether the trained ResNet-18 checkpoint is loaded.
- **5-Class DR Severity Mapping**:
  - Class 0: No Diabetic Retinopathy (No DR)
  - Class 1: Mild Non-Proliferative DR (Mild NPDR)
  - Class 2: Moderate Non-Proliferative DR (Moderate NPDR)
  - Class 3: Severe Non-Proliferative DR (Severe NPDR)
  - Class 4: Proliferative Diabetic Retinopathy (PDR)
- **Mandatory Score Disclaimer**: Top model score is prominently marked with:
  *"Uncalibrated model score, not a true clinical probability."*
- **Grad-CAM Visual Heatmap Attribution**:
  - 3-Way Interactive Toggle: Blended Overlay, Raw Heatmap (Jet Colormap), Original Scan.
  - Saliency Attention Telemetry: Peak coordinate `(X, Y)`, Peak Attention Intensity, Mean Feature Activation, and Salient Area Ratio (>50%).
  - Interpretability Notice: Explains that attention heatmaps indicate model-influencing pixels, not confirmed physical lesions.
- **Audit Ledger Metadata**: Displays session UUID, input resolution, image file size, and SHA-256 hash.
- **Medical Disclaimer**:
  *"Research prototype only — not for diagnosis or clinical decision-making."*

---

## 4. Running Frontend and Backend Together

### Terminal 1: Backend API Service
```bash
# Navigate to project root
cd c:\Users\bhanu\OneDrive\Desktop\MEDVISION

# Start FastAPI server via Uvicorn
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: Frontend Client Service
```bash
# Navigate to frontend folder
cd c:\Users\bhanu\OneDrive\Desktop\MEDVISION\frontend

# Install dependencies if not already installed
npm install

# Start Vite development server
npm run dev
```

Open your browser to: `http://localhost:5173`.
Navigate to **Retinal Module** to upload a retinal fundus image and run RetinaGuard inference.
To create a production build of the frontend:
```bash
npm run build
```

