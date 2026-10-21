# Architecture Documentation — MedVision AI

## 1. System Philosophy & Layer Separation

MedVision AI is engineered around a strict separation of concerns to guarantee safety, reproducibility, and auditability in medical imaging research. 

```mermaid
graph TD
    subgraph Client Tier ["Frontend Client (React + Vite + Tailwind)"]
        UI[User Interface & Modality Selector]
        UploadHook[useImageUpload Hook]
        ApiClient[API Client Service (api.js)]
        UI --> UploadHook --> ApiClient
    end

    subgraph ApiTier ["Backend Service (FastAPI)"]
        CORS[CORS Guard]
        Router[API Routers (v1)]
        Val[File Validator (Format, Size, PIL check)]
        DBService[Metadata & Session Service]
        ApiClient -->|HTTP Multipart / JSON| CORS
        CORS --> Router
        Router --> Val
        Val --> DBService
    end

    subgraph DataTier ["Persistence Tier (SQLite / SQLAlchemy)"]
        DBSession[SessionLocal]
        DBTable[(analysis_sessions Table)]
        DBService --> DBSession --> DBTable
    end

    subgraph AiTier ["AI/ML Tier (Decoupled Engine)"]
        RetinaPipe[ai_models/retina]
        CxrPipe[ai_models/chest_xray]
        Router -.->|Future Hand-off| RetinaPipe
        Router -.->|Future Hand-off| CxrPipe
    end
```

### Responsibility Matrix

| Layer | Directory | Responsibilities | Forbidden Patterns |
| :--- | :--- | :--- | :--- |
| **Frontend** | `frontend/` | UI layout, user interactions, client-side pre-validation, status presentation. | Never include Python code, database credentials, secret keys, or local inference algorithms. |
| **Backend** | `backend/` | Request routing, MIME & size enforcement, session creation, JSON schema responses. | Never fabricate predictions. Never log raw medical image bytes or patient identifiers. |
| **Database** | `database/` | Relational storage for audit sessions, image dimensions, SHA-256 hashes, and future model outputs. | Never store raw image blobs or PII. Never accept direct frontend connections. |
| **AI/ML Engine** | `ai_models/` | Modality-specific preprocessing (CLAHE, Ben Graham), model weights loading, inference, and Grad-CAM generation. | Must remain modular and testable outside of the web server lifecycle. |

---

## 2. Communication Protocol

1. **Protocol**: HTTP/1.1 REST over TCP/IP (development), HTTPS (production).
2. **Payload format**:
   - Client to Backend: `multipart/form-data` with an `image` file field.
   - Backend to Client: `application/json` with RFC-compliant HTTP status codes.
3. **CORS Governance**:
   - Backend strictly admits requests originating from `http://localhost:5173` and `http://127.0.0.1:5173`.
   - Wildcard (`*`) origin access is prohibited to prevent cross-origin data exposure.

---

## 3. Data Flow

1. **Selection**: User drops an image (PNG, JPEG, WebP) into the UI.
2. **Client Validation**: `useImageUpload` verifies the file size ($\le 10$ MB) and MIME type in the browser before network transmission.
3. **Transmission**: The file is sent via `POST` to `/api/v1/retina/analyze` or `/api/v1/chest-xray/analyze`.
4. **Backend Security Validation**:
   - File size header and stream bytes are checked against `MAX_UPLOAD_SIZE_BYTES`.
   - The file header is validated with PIL (`Pillow`) to ensure it is a valid, uncorrupted image.
   - SHA-256 hash is computed in-memory for audit purposes.
5. **Session Creation**: An anonymous UUID session ID is generated and recorded in SQLite alongside metadata.
6. **Placeholder Response**: The backend returns an honest `DEVELOPMENT_PLACEHOLDER` response stating that inference is not yet implemented. Real prediction and explainability fields remain `null`.
