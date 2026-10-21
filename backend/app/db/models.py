"""SQLAlchemy database models for MedVision AI."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Index
from app.db.base import Base


class AnalysisSession(Base):
    """Anonymous research analysis session and image technical metadata model.

    Privacy Invariants:
    1. No raw image pixel arrays or blobs are persisted.
    2. No personally identifiable patient health information is accepted or stored.
    3. Prediction and explanation columns remain NULL until real AI models are verified.
    """

    __tablename__ = "analysis_sessions"

    # Internal Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Public Anonymous Session Token
    session_id = Column(String(36), unique=True, nullable=False, index=True)

    # Modality: 'retina' or 'chest_xray'
    modality = Column(String(32), nullable=False, index=True)

    # Image Technical Metadata
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # In-memory SHA-256
    mime_type = Column(String(64), nullable=False)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)

    # Model Lifecycle
    model_version = Column(String(64), nullable=True)
    status = Column(String(64), nullable=False, default="PENDING_MODEL_INTEGRATION")

    # Real Model Findings (Strictly NULL in development placeholder phase)
    prediction_category = Column(String(128), nullable=True)
    prediction_confidence = Column(Float, nullable=True)
    explanation_text = Column(Text, nullable=True)
    explanation_heatmap_path = Column(String(512), nullable=True)

    # Audit Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("ix_analysis_sessions_modality_created", "modality", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisSession(id='{self.id}', session_id='{self.session_id}', "
            f"modality='{self.modality}', status='{self.status}')>"
        )
