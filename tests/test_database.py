"""Tests for SQLAlchemy database models and constraints."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import AnalysisSession


def test_create_analysis_session(db_session: Session):
    """Test creating an AnalysisSession record adhering to privacy rules."""
    test_session_id = str(uuid.uuid4())
    record = AnalysisSession(
        session_id=test_session_id,
        modality="retina",
        file_name="test_eye.jpg",
        file_size_bytes=1024,
        file_hash="abcd1234ef567890",
        mime_type="image/jpeg",
        image_width=512,
        image_height=512,
        model_version="retina_v0.1_dev_placeholder",
        status="DEVELOPMENT_PLACEHOLDER",
        prediction_category=None,
        prediction_confidence=None,
        explanation_text=None,
        explanation_heatmap_path=None,
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    # Verify persistence & retrieval
    retrieved = db_session.query(AnalysisSession).filter_by(session_id=test_session_id).first()
    assert retrieved is not None
    assert retrieved.modality == "retina"
    assert retrieved.file_name == "test_eye.jpg"
    assert retrieved.prediction_category is None
    assert retrieved.prediction_confidence is None
    assert retrieved.explanation_text is None
