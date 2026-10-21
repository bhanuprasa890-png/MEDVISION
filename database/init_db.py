"""Database initialization utility for MedVision AI.

Reads database/schema.sql and bootstraps the local SQLite database.
Inserts synthetic development records for local verification.
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone


def get_db_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", "medvision.db")


def init_database(db_path: str | None = None) -> str:
    target_path = db_path or get_db_path()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print(f"[+] Initializing database at: {target_path}")
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    # Execute schema statements
    cursor.executescript(schema_sql)
    conn.commit()

    # Insert a synthetic development check record if empty
    cursor.execute("SELECT COUNT(*) FROM analysis_sessions;")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_id = str(uuid.uuid4())
        sample_session = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO analysis_sessions (
                id, session_id, modality, file_name, file_size_bytes,
                file_hash, mime_type, image_width, image_height,
                model_version, status, prediction_category, prediction_confidence,
                explanation_text, explanation_heatmap_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample_id,
                sample_session,
                "retina",
                "synthetic_sample_retina.jpg",
                524288,
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "image/jpeg",
                1024,
                1024,
                "retina_v0.1_dev_placeholder",
                "DEVELOPMENT_PLACEHOLDER",
                None,  # Real prediction unavailable
                None,  # Confidence unavailable
                None,  # Explanation unavailable
                None,  # Heatmap unavailable
                now,
            ),
        )
        conn.commit()
        print(f"[+] Seeded 1 synthetic development audit record (Session ID: {sample_session})")
    else:
        print(f"[i] Database already contains {count} session records.")

    conn.close()
    print("[OK] Database initialized successfully.")
    return target_path


if __name__ == "__main__":
    init_database()
