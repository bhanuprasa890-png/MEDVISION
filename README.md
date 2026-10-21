# MedVision AI — Explainable Medical Imaging Research Assistant

> **Disclaimer:** MedVision AI is an educational and research prototype developed for hackathons and academic inquiry. It is **NOT** a certified medical diagnostic device and must **NEVER** be used for clinical decision-making or real patient diagnosis.

---

## 📌 Project Overview

**MedVision AI** is an open, modular research assistant designed to explore explainable deep learning workflows in medical imaging. The initial milestone establishes a strict four-tier separation of concerns across:

1. **Frontend (`frontend/`)**: React + Vite + Tailwind CSS for UI and API client operations.
2. **Backend (`backend/`)**: Python + FastAPI for asynchronous validation, routing, and metadata tracking.
3. **Database (`database/`)**: SQLite + SQLAlchemy for anonymous session tracking and metadata storage (no PII or raw medical images stored).
4. **AI/ML Engine (`ai_models/`)**: Decoupled pipelines for Retinal Fundus and Chest X-Ray (CXR) imaging with dedicated placeholders for preprocessing, inference, and explainability (Grad-CAM).

---

## 📁 Repository Architecture

```text
MEDVISION/
├── frontend/               # React + Vite + Tailwind CSS web interface
│   ├── src/
│   │   ├── assets/         # Static icons & branding assets
│   │   ├── components/     # Reusable UI components (Uploader, ResultCard, etc.)
│   │   ├── hooks/          # Custom hooks (e.g., useImageUpload)
│   │   ├── pages/          # Application pages (Home, Retina, Chest X-Ray)
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
│   │   ├── core/           # Configuration, security, and CORS policies
│   │   ├── db/             # SQLAlchemy engine, base, and models
│   │   ├── schemas/        # Pydantic request & response validation schemas
│   │   ├── services/       # File validation & business services
│   │   └── main.py         # FastAPI application entry point
│   ├── requirements.txt
│   └── .env.example
├── database/               # Database definitions & initialization scripts
│   ├── schema.sql          # Raw SQL schema definition with indexes
│   ├── init_db.py          # SQLite database bootstrapper
│   └── README.md
├── ai_models/              # AI/ML pipelines (preprocessing, inference, XAI)
│   ├── retina/             # Retinal fundus model pipeline placeholders
│   ├── chest_xray/         # Chest X-Ray model pipeline placeholders
│   └── README.md
├── docs/                   # Architectural & technical documentation
│   ├── architecture.md     # Layer separation & data flow diagrams
│   ├── api-contract.md     # REST endpoints, schemas & error definitions
│   └── database-design.md  # Schema definitions, privacy & indexing rules
├── tests/                  # Automated backend and integration test suite
│   ├── conftest.py         # Pytest fixtures & TestClient configuration
│   ├── test_health.py      # Health check endpoint tests
│   ├── test_file_validation.py # MIME type, size & corruption checks
│   ├── test_retina_endpoint.py # Retina endpoint placeholder tests
│   ├── test_chest_xray_endpoint.py # Chest X-Ray endpoint placeholder tests
│   └── test_database.py    # Database models & transaction tests
├── .env.example            # Root environment variable template
├── .gitignore              # Multi-tier exclusions (.env, *.db, venv, weights)
└── README.md               # Project guide and quickstart
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Node.js**: v18+ (verified with Node.js v24)
- **Python**: 3.10+ (verified with Python 3.13)
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

# Copy environment file
cp .env.example .env

# Run the FastAPI server with hot-reload
uvicorn app.main.py:app --reload --port 8000
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
# Run pytest from the project root or backend directory
cd backend
pytest ../tests -v
```

---

## 🔒 Security & Medical Ethics Principles

- **No Medical Guesswork**: Until verified clinical deep learning weights are integrated, analysis endpoints return transparent, honest development placeholder responses (`DEVELOPMENT_PLACEHOLDER`).
- **Data Privacy (Zero PII)**: We do not store patient names, dates of birth, or hospital identifiers.
- **Stateless Image Analysis**: Uploaded image bytes are processed strictly in-memory for dimension/hash extraction during this milestone; raw pixel data is never persisted to the database.
- **Strict CORS**: Cross-Origin Resource Sharing is locked down to local development origins (`http://localhost:5173`, `http://127.0.0.1:5173`) by default.
