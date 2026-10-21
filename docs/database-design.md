# Database Design — MedVision AI

## 1. Overview & Privacy Architecture

The MedVision AI database is designed to record metadata and audit trails of research interactions without collecting or persisting Personally Identifiable Information (PII) or raw patient medical images.

### Key Privacy Principles:
1. **Zero PII**: No patient names, MRNs (Medical Record Numbers), IP addresses, or demographic markers are recorded.
2. **Stateless Imaging**: Raw uploaded image bytes are never saved to disk or database tables. Only cryptographic hashes (SHA-256) and technical dimensions are stored.
3. **Anonymous Session IDs**: Each interaction is identified by a randomly generated UUID v4 string.
4. **Honest Prediction Nullability**: Prediction and explanation columns are defined as nullable and remain strictly `NULL` until real, clinically verified models are linked.

---

## 2. Table: `analysis_sessions`

The primary entity in SQLite is `analysis_sessions`.

### Schema Definition (SQL)

```sql
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE,
    modality VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(64) NOT NULL,
    image_width INTEGER,
    image_height INTEGER,
    model_version VARCHAR(64),
    status VARCHAR(64) NOT NULL DEFAULT 'PENDING_MODEL_INTEGRATION',
    prediction_category VARCHAR(128),
    prediction_confidence REAL,
    explanation_text TEXT,
    explanation_heatmap_path VARCHAR(512),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON analysis_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_modality ON analysis_sessions(modality);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON analysis_sessions(created_at);
```

### Data Dictionary

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | No | Internal primary key UUID. |
| `session_id` | `VARCHAR(36)` | No | Public unique identifier exposed to client. |
| `modality` | `VARCHAR(32)` | No | Medical imaging modality (`retina`, `chest_xray`). |
| `file_name` | `VARCHAR(255)` | No | Sanitized name of the uploaded image file. |
| `file_size_bytes` | `INTEGER` | No | Size of the image in bytes. |
| `file_hash` | `VARCHAR(64)` | No | SHA-256 hash for auditing & deduplication. |
| `mime_type` | `VARCHAR(64)` | No | Validated MIME type (e.g., `image/jpeg`). |
| `image_width` | `INTEGER` | Yes | Width in pixels parsed from image header. |
| `image_height` | `INTEGER` | Yes | Height in pixels parsed from image header. |
| `model_version` | `VARCHAR(64)` | Yes | Identifies model architecture and checkpoint version. |
| `status` | `VARCHAR(64)` | No | Session lifecycle state (`DEVELOPMENT_PLACEHOLDER`, `PENDING_MODEL_INTEGRATION`). |
| `prediction_category`| `VARCHAR(128)`| Yes | Predicted finding category (strictly `NULL` in placeholder stage). |
| `prediction_confidence`| `REAL` | Yes | Classification score (strictly `NULL` in placeholder stage). |
| `explanation_text` | `TEXT` | Yes | Natural language explanation or attention notes (strictly `NULL`). |
| `explanation_heatmap_path`| `VARCHAR(512)`| Yes | Artifact reference to Grad-CAM heatmap (strictly `NULL`). |
| `created_at` | `TIMESTAMP` | No | UTC timestamp when session was initialized. |

---

## 3. Database Initialization & Migration

### Initialization
To initialize the database locally using the provided script:
```bash
# From workspace root
py database/init_db.py
```
This script runs the DDL script in `database/schema.sql` and generates `medvision.db` with one synthetic development session row for verification.

### Evolution Path
For production scaling, this schema cleanly translates to PostgreSQL. SQLite was selected specifically for simplicity in local hackathon execution without external daemon dependencies.
