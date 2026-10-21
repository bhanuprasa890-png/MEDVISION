# MedVision AI — FastAPI Backend Service

## 1. Overview
The backend service manages HTTP request routing, in-memory image validation, anonymous session recording via SQLAlchemy, and responses for medical imaging research pipelines.

---

## 2. Directory Layout
```text
backend/
├── app/
│   ├── api/            # API endpoints & routing (v1)
│   ├── core/           # Configuration, security & CORS
│   ├── db/             # SQLAlchemy engine, session & models
│   ├── schemas/        # Pydantic request/response validation
│   ├── services/       # File validation & business logic
│   └── main.py         # FastAPI application entry point
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # Backend service documentation
```

---

## 3. Running Locally

```bash
# From the backend directory
# 1. Create a virtual environment
py -m venv venv

# 2. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Unix / macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy configuration
cp .env.example .env

# 5. Start development server
uvicorn app.main:app --reload --port 8000
```

- API Docs (Swagger): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`
