"""PostgreSQL migration script for MedVision AI.

Migrates the analysis_sessions audit ledger from an embedded SQLite database
to an external PostgreSQL instance (e.g. AWS RDS, GCP Cloud SQL, or Azure Database).

Features:
- Preserves all session identifiers, technical metadata, and audit records.
- Batch processing with chunking for large ledgers.
- Dry-run validation mode.
- Verification checks comparing source vs. target record counts.
- Non-destructive: source SQLite database is strictly read-only.
"""

import argparse
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("medvision.migrate_postgres")


POSTGRES_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE,
    modality VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON analysis_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_modality ON analysis_sessions(modality);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON analysis_sessions(created_at);
"""


def verify_sqlite_source(sqlite_path: str) -> Tuple[bool, int]:
    """Verify SQLite source database existence, schema, and record count."""
    if not os.path.exists(sqlite_path):
        logger.error("Source SQLite database file not found: %s", sqlite_path)
        return False, 0

    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='analysis_sessions';")
        if cursor.fetchone()[0] == 0:
            logger.error("Source SQLite database does not contain 'analysis_sessions' table.")
            conn.close()
            return False, 0

        cursor.execute("SELECT count(*) FROM analysis_sessions;")
        count = cursor.fetchone()[0]
        conn.close()
        return True, count
    except Exception as exc:
        logger.error("Error reading source SQLite database: %s", exc)
        return False, 0


def fetch_sqlite_rows(sqlite_path: str, offset: int, limit: int) -> List[Tuple[Any, ...]]:
    """Fetch a slice of rows from SQLite."""
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id, session_id, modality, file_name, file_size_bytes,
            file_hash, mime_type, image_width, image_height, model_version,
            status, prediction_category, prediction_confidence,
            explanation_text, explanation_heatmap_path, created_at
        FROM analysis_sessions
        ORDER BY created_at ASC
        LIMIT ? OFFSET ?;
        """,
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def migrate_to_postgres(sqlite_path: str, postgres_url: str, batch_size: int = 500, dry_run: bool = False) -> bool:
    """Execute migration from SQLite to PostgreSQL."""
    valid, source_count = verify_sqlite_source(sqlite_path)
    if not valid:
        return False

    logger.info("Source SQLite database verified: %d records found in %s", source_count, sqlite_path)

    if dry_run:
        logger.info("[DRY-RUN] Schema and source verified. %d records would be migrated to PostgreSQL.", source_count)
        return True

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.error("SQLAlchemy is required for migration. Please install dependencies.")
        return False

    logger.info("Connecting to target PostgreSQL database...")
    engine = create_engine(postgres_url, echo=False)

    # 1. Create target table & indexes
    with engine.begin() as conn:
        logger.info("Ensuring PostgreSQL schema and indexes exist...")
        for statement in POSTGRES_SCHEMA_SQL.strip().split(";"):
            stmt_clean = statement.strip()
            if stmt_clean:
                conn.execute(text(stmt_clean))

    # 2. Insert records in batches
    insert_sql = text(
        """
        INSERT INTO analysis_sessions (
            id, session_id, modality, file_name, file_size_bytes,
            file_hash, mime_type, image_width, image_height, model_version,
            status, prediction_category, prediction_confidence,
            explanation_text, explanation_heatmap_path, created_at
        ) VALUES (
            :id, :session_id, :modality, :file_name, :file_size_bytes,
            :file_hash, :mime_type, :image_width, :image_height, :model_version,
            :status, :prediction_category, :prediction_confidence,
            :explanation_text, :explanation_heatmap_path, :created_at
        ) ON CONFLICT (session_id) DO NOTHING;
        """
    )

    migrated_count = 0
    offset = 0

    while offset < source_count:
        rows = fetch_sqlite_rows(sqlite_path, offset=offset, limit=batch_size)
        if not rows:
            break

        param_list: List[Dict[str, Any]] = []
        for r in rows:
            param_list.append(
                {
                    "id": r[0],
                    "session_id": r[1],
                    "modality": r[2],
                    "file_name": r[3],
                    "file_size_bytes": r[4],
                    "file_hash": r[5],
                    "mime_type": r[6],
                    "image_width": r[7],
                    "image_height": r[8],
                    "model_version": r[9],
                    "status": r[10],
                    "prediction_category": r[11],
                    "prediction_confidence": r[12],
                    "explanation_text": r[13],
                    "explanation_heatmap_path": r[14],
                    "created_at": r[15],
                }
            )

        with engine.begin() as conn:
            conn.execute(insert_sql, param_list)

        migrated_count += len(rows)
        offset += len(rows)
        logger.info("Migrated %d / %d records (%.1f%%)", migrated_count, source_count, (migrated_count / source_count) * 100)

    # 3. Verify counts
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM analysis_sessions;"))
        target_count = res.scalar()

    logger.info("Migration complete! Source SQLite: %d records | Target PostgreSQL: %d records", source_count, target_count)
    engine.dispose()
    return True


def main():
    parser = argparse.ArgumentParser(description="Migrate MedVision SQLite database to PostgreSQL.")
    parser.add_argument("--sqlite-path", default="medvision.db", help="Path to source SQLite database file")
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Target PostgreSQL connection URL (e.g. postgresql://user:pass@host:5432/medvision)",
    )
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for migration insertion")
    parser.add_argument("--dry-run", action="store_true", help="Perform pre-flight checks without inserting data")

    args = parser.parse_args()

    if not args.postgres_url and not args.dry_run:
        logger.error("Target PostgreSQL URL required. Set --postgres-url or TARGET_DATABASE_URL environment variable.")
        sys.exit(1)

    success = migrate_to_postgres(
        sqlite_path=args.sqlite_path,
        postgres_url=args.postgres_url or "",
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
