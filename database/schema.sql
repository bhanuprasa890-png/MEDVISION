-- =============================================================================
-- MedVision AI — Database Schema (SQLite)
-- Explainable Medical Imaging Research Assistant
-- =============================================================================
-- Privacy & Compliance Architecture:
-- 1. No Personally Identifiable Information (PII) is stored.
-- 2. No raw image pixel data or medical records are persisted.
-- 3. Only image metadata (dimensions, hash, size) and session audit logs are retained.
-- 4. Prediction and explanation fields remain NULL until a real model is integrated.
-- =============================================================================

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

-- Optimize queries by session_id, modality, and creation timestamp
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON analysis_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_modality ON analysis_sessions(modality);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON analysis_sessions(created_at);
