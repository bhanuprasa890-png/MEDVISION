"""Pydantic schemas for MedAssist health-education conversational service."""

from datetime import datetime, timezone
import math
import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Standard UUID pattern (hex 8-4-4-4-12, total 36 chars with hyphens)
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Canonical Diabetic Retinopathy classes and accepted aliases
VALID_DR_CLASSES: Dict[int, List[str]] = {
    0: ["no diabetic retinopathy", "no dr", "normal", "none"],
    1: ["mild non-proliferative dr", "mild npdr", "mild non-proliferative diabetic retinopathy", "mild", "mild dr"],
    2: ["moderate non-proliferative dr", "moderate npdr", "moderate non-proliferative diabetic retinopathy", "moderate", "moderate dr"],
    3: ["severe non-proliferative dr", "severe npdr", "severe non-proliferative diabetic retinopathy", "severe", "severe dr"],
    4: ["proliferative diabetic retinopathy", "proliferative dr", "pdr", "proliferative"],
}

ALL_DR_ALIASES = [alias for aliases in VALID_DR_CLASSES.values() for alias in aliases]


class ChatMessage(BaseModel):
    """Single conversational turn in browser session history."""
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"] = Field(
        ...,
        description="Role of the speaker (user or assistant)",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=15000,
        description="Text content of the message (bounded to 15,000 chars to accommodate detailed assistant responses in history)",
    )
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message creation timestamp",
    )


class ScanContext(BaseModel):
    """Minimal, typed scan context for optional educational explanation.

    Security & Privacy Invariants:
    1. Strictly forbids unexpected or injected fields via extra='forbid'.
    2. Excludes raw image pixel bytes, base64 payloads, or binary streams.
    3. Excludes patient names, MRNs, health record IDs, or study dates.
    4. Excludes uploaded file names or file system paths.
    5. Validates session_id as legitimate UUID format matching application generator.
    6. Rejects NaN, +Inf, -Inf, and enforces strict numeric score bounds [0.0, 1.0].
    7. Validates consistency between predicted class index, label, and score distribution.
    8. Strictly restricts modality to integrated 'retina' pipeline.
    """
    model_config = ConfigDict(extra="forbid")

    modality: Literal["retina"] = Field(
        default="retina",
        description="Imaging modality (currently strictly 'retina')",
    )
    predicted_class: Optional[int] = Field(
        None,
        ge=0,
        le=4,
        description="Model output class integer index (0-4 for retina)",
    )
    class_label: Optional[str] = Field(
        None,
        max_length=120,
        description="Dataset diagnostic label (e.g. 'Moderate Non-Proliferative DR')",
    )
    severity_level: Optional[str] = Field(
        None,
        max_length=120,
        description="Clinical DR severity grade description if available",
    )
    model_version: Optional[str] = Field(
        None,
        max_length=100,
        description="Verified neural architecture/version identifier",
    )
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Uncalibrated softmax output score (0.0 to 1.0)",
    )
    all_class_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Uncalibrated model score distribution across candidate classes (max 10 entries)",
    )
    session_id: Optional[str] = Field(
        None,
        max_length=36,
        description="Legitimate UUID session token from the analysis audit ledger",
    )

    @field_validator("modality", mode="before")
    @classmethod
    def validate_modality(cls, v: Optional[str]) -> str:
        mod = str(v).strip().lower() if v else "retina"
        if mod == "chest_xray":
            raise ValueError(
                "Chest X-ray scan context is not currently supported for MedAssist integration. "
                "Only 'retina' is supported."
            )
        if mod != "retina":
            raise ValueError(f"Unsupported modality '{v}'. Only 'retina' is supported.")
        return "retina"

    @field_validator("class_label", "severity_level", mode="before")
    @classmethod
    def sanitize_text_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        text = str(v).strip()
        if not text:
            return None
        injection_patterns = [
            r"ignore\s+(previous|all)\s+instructions",
            r"system\s+prompt",
            r"disregard",
            r"<\s*script",
            r"javascript:",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("Text contains forbidden or suspicious content.")
        return text

    @field_validator("session_id", mode="before")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = str(v).strip()
        if not cleaned:
            return None
        if len(cleaned) != 36 or not UUID_PATTERN.match(cleaned):
            raise ValueError(
                "session_id must be a valid 36-character UUID string (e.g. 'c9b5d38f-9a3b-4c6e-821f-13d8560129bc')."
            )
        return cleaned.lower()

    @field_validator("confidence_score", mode="before")
    @classmethod
    def validate_confidence_score(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        try:
            score_f = float(v)
        except (ValueError, TypeError):
            raise ValueError("confidence_score must be a finite float.")
        if not math.isfinite(score_f):
            raise ValueError("confidence_score must be a finite number (NaN and Inf are forbidden).")
        if score_f < 0.0 or score_f > 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0.")
        return round(score_f, 4)

    @field_validator("all_class_scores", mode="before")
    @classmethod
    def validate_class_scores(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("all_class_scores must be a dictionary.")
        if len(v) > 10:
            raise ValueError("all_class_scores contains too many entries (max 10).")

        valid_index_keys = {"0", "1", "2", "3", "4"}
        validated: Dict[str, float] = {}
        for k, score in v.items():
            clean_k = str(k).strip()[:50]
            clean_k_lower = clean_k.lower()
            if clean_k_lower not in valid_index_keys and not any(alias in clean_k_lower for alias in ALL_DR_ALIASES):
                raise ValueError(f"Invalid class key '{clean_k}' in all_class_scores.")

            try:
                score_f = float(score)
            except (ValueError, TypeError):
                raise ValueError(f"Score for class '{clean_k}' must be a float.")
            if not math.isfinite(score_f):
                raise ValueError(f"Score for class '{clean_k}' must be a finite number (NaN and Inf are forbidden).")
            if score_f < 0.0 or score_f > 1.0:
                raise ValueError(f"Score for class '{clean_k}' must be between 0.0 and 1.0.")
            validated[clean_k] = round(score_f, 4)
        return validated

    @model_validator(mode="after")
    def validate_consistency(self) -> "ScanContext":
        """Validate consistency across predicted_class, class_label, and scores."""
        # 1. Validate class_label matches valid DR vocabulary
        if self.class_label:
            clean_label = self.class_label.strip().lower()
            if not any(alias in clean_label for alias in ALL_DR_ALIASES):
                raise ValueError(
                    f"Unrecognized class_label '{self.class_label}' for RetinaGuard DR classification."
                )

        # 2. Validate correspondence between predicted_class and class_label
        if self.predicted_class is not None and self.class_label:
            allowed_aliases = VALID_DR_CLASSES.get(self.predicted_class, [])
            clean_label = self.class_label.strip().lower()
            if not any(alias in clean_label for alias in allowed_aliases):
                raise ValueError(
                    f"Inconsistent scan context: predicted_class Class {self.predicted_class} "
                    f"does not correspond to class_label '{self.class_label}'."
                )

        # 3. Validate correspondence between predicted_class, confidence_score, and all_class_scores
        if self.all_class_scores and self.predicted_class is not None:
            pred_key = str(self.predicted_class)
            if pred_key in self.all_class_scores:
                pred_score = self.all_class_scores[pred_key]
                max_score = max(self.all_class_scores.values())
                if pred_score < (max_score - 0.02):
                    raise ValueError(
                        f"Inconsistent scan context: predicted_class Class {self.predicted_class} "
                        f"has score {pred_score:.4f}, but highest class score is {max_score:.4f}."
                    )
                if self.confidence_score is not None and abs(self.confidence_score - pred_score) > 0.05:
                    raise ValueError(
                        f"Inconsistent scan context: confidence_score {self.confidence_score:.4f} "
                        f"does not match score {pred_score:.4f} for Class {self.predicted_class}."
                    )
        return self


class ChatRequest(BaseModel):
    """Payload for conversational queries to MedAssist."""
    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User health-education query text (bounded to max 1000 chars)",
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Recent session conversational history turns (max 20 items)",
    )
    scan_context: Optional[ScanContext] = Field(
        default=None,
        description="Validated non-identifiable scan context",
    )
    language: Optional[str] = Field(
        default="en",
        max_length=15,
        pattern=r"^[a-zA-Z]{2,5}(-[a-zA-Z0-9]{2,8})?$",
        description="User language preference code (e.g. 'en', 'ta', 'hi', 'te')",
    )

    @field_validator("language", mode="before")
    @classmethod
    def sanitize_language(cls, v: Optional[str]) -> str:
        if v is None:
            return "en"
        if isinstance(v, str) and not v.strip():
            return "en"
        if isinstance(v, str):
            return v.strip().lower()
        return "en"


class ChatResponse(BaseModel):
    """Response payload returned by MedAssist conversational engine."""

    message: str = Field(
        ...,
        description="Educational response text generated by genuine LLM provider",
    )
    provider: str = Field(
        ...,
        description="Name of configured LLM provider ('gemini' or 'openai')",
    )
    model: str = Field(
        ...,
        description="Model identifier used for generation",
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback provider was used to generate this response",
    )
    disclaimer: str = Field(
        default=(
            "EDUCATIONAL RESEARCH USE ONLY: Not a clinical diagnosis, medical directive, "
            "or treatment plan. Always consult a qualified physician or eye-care specialist "
            "for personal health concerns or urgent symptoms."
        ),
        description="Mandatory medical safety disclaimer attached to all conversational responses",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC generation timestamp",
    )


class ChatStatusResponse(BaseModel):
    """Readiness status of the MedAssist conversational service."""

    status: str = Field(
        ...,
        description="'ready' if genuine LLM provider is configured, otherwise 'unconfigured'",
    )
    provider: str = Field(
        ...,
        description="Configured provider ('gemini', 'openai', or 'none')",
    )
    model: str = Field(
        ...,
        description="Active LLM model identifier",
    )
    is_configured: bool = Field(
        ...,
        description="Boolean indicating whether MedAssist has valid provider credentials",
    )
    fallback_configured: bool = Field(
        default=False,
        description="Whether secondary fallback provider is configured",
    )
    fallback_provider: Optional[str] = Field(
        default=None,
        description="Name of configured fallback provider, if any",
    )
    disclaimer: str = Field(
        default=(
            "RESEARCH ONLY: MedAssist provides health-education and terminology explanations. "
            "Never used for patient diagnosis or clinical decision-making."
        ),
        description="Service boundary disclaimer",
    )
