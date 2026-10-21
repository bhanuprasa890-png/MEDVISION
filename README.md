# MEDVISION — Explainable Medical Imaging Research Assistant

> **AI-assisted retinal and chest X-ray research application and clinical explainability prototype.**
> 
> **Disclaimer:** MedVision AI is an educational and research prototype developed for academic inquiry and laboratory experimentation. It is **NOT** a certified medical diagnostic device and must **NEVER** be used for clinical decision-making or real patient diagnosis.

---

## 📌 Project Overview

**MedVision AI** is an open, modular research assistant designed to explore explainable deep learning workflows in medical imaging. The system establishes a strict four-tier separation of concerns across:

1. **Frontend (`frontend/`)**: React 18 + Vite + Tailwind CSS for UI, interactive Grad-CAM visualization, and API client operations.
2. **Backend (`backend/`)**: Python + FastAPI for asynchronous validation, rate limiting, routing, and metadata tracking.
3. **Database (`database/`)**: SQLite + SQLAlchemy (WAL mode) for anonymous session tracking and metadata storage (no PII or raw medical images stored).
4. **AI/ML Engine (`ai_models/`)**: Decoupled pipelines for Retinal Fundus (Diabetic Retinopathy) and Chest Radiographs (18 pathologies) with Grad-CAM visual attribution heatmaps.

---

## 📁 Repository Architecture

```text
MEDVISION/
├── frontend/               # React + Vite + Tailwind CSS web interface
│   ├── src/
│   │   ├── assets/         # Static icons & branding assets
│   │   ├── components/     # Reusable UI components (Uploader, ResultCard, etc.)
│   │   ├── hooks/          # Custom hooks (e.g., useImageUpload)
│   │   ├── pages/          # Application pages (Home, Retina, Chest X-Ray, MedAssist)
│   │   ├── services/       # API client abstractions (fetch wrappers)
│   │   ├── App.jsx         # App shell & routing
│   │   ├── main.jsx        # React root mount
│   │   └── index.css       # Tailwind CSS directives
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/                # Python + FastAPI backend service
│   ├── app/
│   │   ├── api/            # API endpoints (/api/health, /api/v1/...)
│   │   ├── core/           # Configuration, security, rate limiting, and CORS
│   │   ├── db/             # SQLAlchemy engine, base, and models
│   │   ├── schemas/        # Pydantic request & response validation schemas
│   │   ├── services/       # File validation, chat service & model inference
│   │   └── main.py         # FastAPI application entry point
│   ├── requirements.txt
│   └── .env.example
├── database/               # Database definitions & initialization scripts
│   ├── schema.sql          # Raw SQL schema definition with indexes
│   ├── init_db.py          # SQLite database bootstrapper
│   ├── migrate_to_postgres.py # PostgreSQL migration engine
│   └── README.md
├── ai_models/              # AI/ML pipelines (preprocessing, inference, XAI)
│   ├── retina/             # Retinal fundus ResNet-18 pipeline & Grad-CAM
│   ├── chest_xray/         # Chest X-Ray DenseNet-121 pipeline & Grad-CAM
│   └── README.md
├── docs/                   # Architectural & technical documentation
│   ├── architecture.md     # Layer separation & data flow diagrams
│   ├── api-contract.md     # REST endpoints, schemas & error definitions
│   └── database-design.md  # Schema definitions, privacy & indexing rules
├── tests/                  # Automated backend and integration test suite (55+ tests)
│   ├── conftest.py         # Pytest fixtures & TestClient configuration
│   ├── test_health.py      # Health check endpoint tests
│   ├── test_file_validation.py # MIME type, size & corruption checks
│   ├── test_retina_endpoint.py # Retina endpoint & model evaluation tests
│   ├── test_chest_xray_endpoint.py # Chest X-Ray endpoint tests
│   ├── test_security_audit.py  # Security, rate limiting & auth tests
│   ├── test_staging_verification.py # 20-point staging verification suite
│   └── test_database.py    # Database models & transaction tests
├── DEPLOYMENT.md           # Production, staging & operational runbooks
├── .env.example            # Root environment variable template
├── .gitignore              # Multi-tier exclusions (.env, *.db, venv, weights)
└── README.md               # Project guide and quickstart
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Node.js**: v18+ (tested on Node.js v24)
- **Python**: 3.10+ (tested on Python 3.13)
- **pip** / **venv**

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate a Python virtual environment (Windows PowerShell)
py -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the FastAPI server with hot-reload
uvicorn app.main:app --reload --port 8000
```
- API Health Endpoint: `http://localhost:8000/api/health`
- Swagger Interactive Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
- Frontend application URL: `http://localhost:5173`

### 4. Running the Test Suite
```bash
# Backend pytest suite (from project root)
pytest tests/ -v

# Frontend test suite (from frontend directory)
cd frontend
npm test
```

---

## 🔒 Security & Medical Ethics Principles

- **No Medical Guesswork**: Inference pipelines provide clear class probabilities and visual attribution heatmaps, without fabricated certainty or clinical diagnoses.
- **Data Privacy (Zero PII)**: No patient names, dates of birth, or hospital identifiers are ever collected or stored.
- **Stateless Image Analysis**: Uploaded image bytes are processed in-memory for inference and Grad-CAM generation; raw pixel files are never persisted to the database.
- **Strict CORS & Rate Limiting**: Cross-Origin Resource Sharing is locked down to configured origins, and distributed sliding-window rate limiting prevents API abuse.
