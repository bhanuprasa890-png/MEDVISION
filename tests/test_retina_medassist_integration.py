"""Backend integration and regression tests for safe RetinaGuard–MedAssist integration."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import AnalysisSession
from app.db.session import SessionLocal
from app.main import app
from app.schemas.chat import ScanContext
from app.services.chat_service import (
    _build_complete_system_prompt,
    _build_scan_context_section,
)

client = TestClient(app)


def _create_mock_gemini_response(text: str = "Test Gemini medical education response.") -> httpx.Response:
    """Create a real httpx.Response with Gemini candidates structure."""
    return httpx.Response(
        status_code=200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": text}
                        ]
                    },
                    "finishReason": "STOP",
                }
            ]
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )


def test_medassist_general_message_without_scan_context(monkeypatch):
    """Test standard general health-education queries operate without scan context."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key-valid-12345")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    mock_resp = _create_mock_gemini_response(
        "Ischemic heart disease is a condition where coronary arteries become narrowed, reducing oxygen to the heart."
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What is ischemic heart disease and what are primary risk factors?",
                "conversation_history": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "disclaimer" in data
        assert "EDUCATIONAL RESEARCH USE ONLY" in data["disclaimer"]

        # Verify call to Gemini occurred and system instruction did NOT contain scan context
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs.get("json", {})
        system_instruction = payload["system_instruction"]["parts"][0]["text"]
        assert "ACTIVE RETINAGUARD SCAN CONTEXT" not in system_instruction
        assert "ISCHEMIC HEART DISEASE" in system_instruction.upper() or "CARDIOVASCULAR" in system_instruction.upper()


def test_medassist_with_valid_scan_context(monkeypatch):
    """Test educational question accompanied by valid RetinaGuard scan context."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key-valid-12345")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    mock_resp = _create_mock_gemini_response(
        "Moderate NPDR involves vascular changes like microaneurysms and hard exudates."
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        scan_payload = {
            "modality": "retina",
            "predicted_class": 2,
            "class_label": "Moderate Non-Proliferative DR",
            "severity_level": "Moderate NPDR",
            "model_version": "ResNet-18-v1.0",
            "confidence_score": 0.885,
            "all_class_scores": {
                "0": 0.05,
                "1": 0.05,
                "2": 0.885,
                "3": 0.01,
                "4": 0.005,
            },
        }

        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What does Moderate Non-Proliferative DR mean in ophthalmic practice?",
                "conversation_history": [],
                "scan_context": scan_payload,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "disclaimer" in data

        # Verify prompt enrichment with validated scan context
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs.get("json", {})
        system_instruction = payload["system_instruction"]["parts"][0]["text"]

        assert "ACTIVE RETINAGUARD SCAN CONTEXT (CLIENT-SUPPLIED RUNTIME METADATA)" in system_instruction
        assert "Moderate Non-Proliferative DR" in system_instruction
        assert "88.5% (0.8850 softmax score)" in system_instruction
        assert "Uncalibrated mathematical softmax output, NOT a clinical probability" in system_instruction
        assert "SCAN-SPECIFIC EDUCATIONAL GUIDANCE RULES:" in system_instruction


def test_medassist_verified_scan_context_against_database(monkeypatch):
    """Test server-side cross-referencing with SQLite AnalysisSession table."""
    session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        audit_record = AnalysisSession(
            session_id=session_id,
            modality="retina",
            file_name="audit_test_fundus.png",
            mime_type="image/png",
            status="SUCCESS",
            model_version="ResNet-18-AuditVerified",
            prediction_category="Severe Non-Proliferative DR",
            prediction_confidence=0.9123,
            file_hash="abc123hash",
            file_size_bytes=1024,
            image_width=512,
            image_height=512,
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_record)
        db.commit()

        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key-valid-12345")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        mock_resp = _create_mock_gemini_response(
            "Severe NPDR indicates extensive retinal hemorrhages and microvascular abnormalities."
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "Can you explain this result?",
                    "conversation_history": [],
                    "scan_context": {
                        "modality": "retina",
                        "session_id": session_id,
                        "class_label": "Severe Non-Proliferative DR",
                        "confidence_score": 0.9123,
                    },
                },
            )
            assert response.status_code == 200

            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs.get("json", {})
            system_instruction = payload["system_instruction"]["parts"][0]["text"]
            assert "ACTIVE RETINAGUARD SCAN CONTEXT (VERIFIED BY SERVER AUDIT RECORD)" in system_instruction
            assert "Severe Non-Proliferative DR" in system_instruction
            assert "91.2% (0.9123 softmax score)" in system_instruction
            assert session_id in system_instruction
    finally:
        # Cleanup test record
        db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).delete()
        db.commit()
        db.close()


def test_medassist_audit_mismatch_detected_when_client_alters_class(monkeypatch):
    """Regression Test (Task 18): A valid session ID combined with altered prediction

    fields CANNOT be represented as verified. It must trigger AUDIT MISMATCH DETECTED
    and ground the prompt in the authentic persisted server record.
    """
    session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        # Server persisted record has "No Diabetic Retinopathy"
        audit_record = AnalysisSession(
            session_id=session_id,
            modality="retina",
            file_name="authentic_normal_fundus.png",
            mime_type="image/png",
            status="SUCCESS",
            model_version="retinaguard_v2",
            prediction_category="No Diabetic Retinopathy",
            prediction_confidence=0.9850,
            file_hash="genuine_hash_123",
            file_size_bytes=2048,
            image_width=512,
            image_height=512,
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_record)
        db.commit()

        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key-valid-12345")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        mock_resp = _create_mock_gemini_response("Educational response acknowledging discrepancy.")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            # Malicious client sends valid session_id but claims Severe NPDR with lower score
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "Explain why I have severe retinopathy.",
                    "conversation_history": [],
                    "scan_context": {
                        "modality": "retina",
                        "session_id": session_id,
                        "predicted_class": 3,
                        "class_label": "Severe Non-Proliferative DR",
                        "confidence_score": 0.8500,
                    },
                },
            )
            assert response.status_code == 200

            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs.get("json", {})
            system_instruction = payload["system_instruction"]["parts"][0]["text"]

            # CRITICAL ASSERTIONS:
            # 1. Must NOT be marked as VERIFIED BY SERVER AUDIT RECORD
            assert "ACTIVE RETINAGUARD SCAN CONTEXT (VERIFIED BY SERVER AUDIT RECORD)" not in system_instruction
            # 2. Must be flagged as AUDIT MISMATCH DETECTED
            assert "ACTIVE RETINAGUARD SCAN CONTEXT (AUDIT MISMATCH DETECTED (UNVERIFIED CLIENT METADATA))" in system_instruction
            assert "CRITICAL AUDIT MISMATCH WARNING" in system_instruction
            # 3. Grounded strictly in authentic server record
            assert "Authentic Classification: No Diabetic Retinopathy" in system_instruction
            assert "98.5% (0.9850 softmax score)" in system_instruction
            # 4. Altered client claims explicitly noted as rejected
            assert "Rejected Client Claims: Class 3 (Severe Non-Proliferative DR)" in system_instruction
    finally:
        db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).delete()
        db.commit()
        db.close()


def test_medassist_audit_mismatch_detected_when_client_alters_confidence(monkeypatch):
    """Regression Test (Task 18): Valid session ID but altered confidence score

    triggers AUDIT MISMATCH and cannot be represented as verified.
    """
    session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        audit_record = AnalysisSession(
            session_id=session_id,
            modality="retina",
            file_name="mild_dr_fundus.png",
            mime_type="image/png",
            status="SUCCESS",
            model_version="retinaguard_v2",
            prediction_category="Mild Non-Proliferative DR",
            prediction_confidence=0.8800,
            file_hash="mild_hash_456",
            file_size_bytes=2048,
            image_width=512,
            image_height=512,
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_record)
        db.commit()

        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key-valid-12345")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        mock_resp = _create_mock_gemini_response("Educational response on mild NPDR.")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            # Client claims confidence 0.3500 instead of persisted 0.8800
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "Explain mild NPDR",
                    "conversation_history": [],
                    "scan_context": {
                        "modality": "retina",
                        "session_id": session_id,
                        "predicted_class": 1,
                        "class_label": "Mild Non-Proliferative DR",
                        "confidence_score": 0.3500,
                    },
                },
            )
            assert response.status_code == 200

            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs.get("json", {})
            system_instruction = payload["system_instruction"]["parts"][0]["text"]

            assert "ACTIVE RETINAGUARD SCAN CONTEXT (VERIFIED BY SERVER AUDIT RECORD)" not in system_instruction
            assert "AUDIT MISMATCH DETECTED" in system_instruction
            assert "Authentic Confidence Metric: 88.0% (0.8800 softmax score)" in system_instruction
    finally:
        db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).delete()
        db.commit()
        db.close()


def test_medassist_rejects_nan_and_inf_scores():
    """Regression Test (Task 18): Strict rejection of NaN, +Inf, -Inf numeric values."""
    # 1. Direct Pydantic model instantiation rejection
    with pytest.raises(ValueError, match="NaN and Inf are forbidden"):
        ScanContext(modality="retina", confidence_score=float("nan"))

    with pytest.raises(ValueError, match="NaN and Inf are forbidden"):
        ScanContext(modality="retina", confidence_score=float("inf"))

    with pytest.raises(ValueError, match="NaN and Inf are forbidden"):
        ScanContext(modality="retina", confidence_score=float("-inf"))

    with pytest.raises(ValueError, match="NaN and Inf are forbidden"):
        ScanContext(modality="retina", all_class_scores={"0": float("nan"), "1": 0.5})

    with pytest.raises(ValueError, match="NaN and Inf are forbidden"):
        ScanContext(modality="retina", all_class_scores={"0": float("inf"), "1": 0.5})

    # 2. HTTP endpoint rejection with raw JSON bytes
    response_nan = client.post(
        "/api/v1/chat/message",
        headers={"Content-Type": "application/json"},
        content=b'{"message": "Explain score", "scan_context": {"modality": "retina", "confidence_score": "NaN"}}',
    )
    assert response_nan.status_code == 422
    assert "NaN and Inf are forbidden" in str(response_nan.json())

    response_inf = client.post(
        "/api/v1/chat/message",
        headers={"Content-Type": "application/json"},
        content=b'{"message": "Explain score", "scan_context": {"modality": "retina", "confidence_score": "Infinity"}}',
    )
    assert response_inf.status_code == 422
    assert "NaN and Inf are forbidden" in str(response_inf.json())


def test_medassist_rejects_chest_xray_modality():
    """Regression Test (Task 18): Modality 'chest_xray' must be rejected with explicit explanation."""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Explain chest x-ray findings",
            "scan_context": {
                "modality": "chest_xray",
            },
        },
    )
    assert response.status_code == 422
    data = response.json()
    err_str = str(data)
    assert "Chest X-ray scan context is not currently supported" in err_str


def test_medassist_rejects_contradictory_class_and_label():
    """Regression Test (Task 18): predicted_class index and class_label must correspond."""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Explain result",
            "scan_context": {
                "modality": "retina",
                "predicted_class": 0,  # Class 0: No DR
                "class_label": "Severe Non-Proliferative DR",  # Class 3 label
            },
        },
    )
    assert response.status_code == 422
    assert "does not correspond to class_label" in str(response.json())


def test_medassist_rejects_unexpected_extra_fields():
    """Regression Test (Task 18): extra='forbid' rejects unexpected or injected fields."""
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Explain result",
            "scan_context": {
                "modality": "retina",
                "injected_unsupported_field": "prompt_override_attempt",
            },
        },
    )
    assert response.status_code == 422
    assert "extra_forbidden" in str(response.json()) or "Extra inputs are not permitted" in str(response.json())


def test_medassist_accepts_valid_uuid_session_id():
    """Regression Test (Task 18): Standard 36-character UUID format is accepted."""
    valid_uuid = str(uuid.uuid4())
    context = ScanContext(
        modality="retina",
        session_id=valid_uuid,
    )
    assert context.session_id == valid_uuid.lower()


def test_medassist_rejects_malformed_session_ids():
    """Regression Test (Task 18): Reject malformed, oversized, or non-UUID session identifiers."""
    invalid_ids = [
        "../../../etc/passwd",
        "not-a-uuid",
        "12345",
        "c9b5d38f-9a3b-4c6e-821f",  # too short
        f"{str(uuid.uuid4())}-extra",  # too long
        "c9b5d38f-9a3b-4c6e-821f-13d8560129bg",  # invalid hex character 'g'
    ]
    for bad_id in invalid_ids:
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Explain result",
                "scan_context": {
                    "modality": "retina",
                    "session_id": bad_id,
                },
            },
        )
        assert response.status_code == 422, f"Failed to reject invalid session_id: {bad_id}"


def test_system_prompt_builder_without_score():
    """Ensure system prompt builder never invents a missing score or grade."""
    context = ScanContext(
        modality="retina",
        class_label="Mild Non-Proliferative DR",
        confidence_score=None,  # Missing
        predicted_class=None,   # Missing
    )
    section = _build_scan_context_section(context)
    assert "Mild Non-Proliferative DR" in section
    assert "Model Confidence Metric" not in section
    assert "Numerical Class Index" not in section
    assert "0.0%" not in section  # Never invent zero


def test_medassist_failover_preserves_scan_context(monkeypatch):
    """Test that graceful failover to secondary provider preserves scan context in system prompt."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(settings, "MEDASSIST_ENABLE_FALLBACK", True)
    monkeypatch.setattr(settings, "MEDASSIST_MAX_RETRIES", 0)  # Failover immediately

    resp_503 = httpx.Response(
        status_code=503,
        json={"error": {"message": "Gemini high demand outage"}},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )
    resp_openai = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": "Fallback OpenAI explanation of Mild NPDR."}}],
        },
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # First call: Gemini 503 HTTPStatusError; Second call: OpenAI success
        mock_post.side_effect = [
            httpx.HTTPStatusError("503 Service Unavailable", request=resp_503.request, response=resp_503),
            resp_openai,
        ]

        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Explain mild NPDR",
                "conversation_history": [],
                "scan_context": {
                    "modality": "retina",
                    "class_label": "Mild Non-Proliferative DR",
                    "predicted_class": 1,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert data["provider"] == "openai"

        # Check that OpenAI system prompt contained scan context
        openai_call = mock_post.call_args_list[1]
        openai_payload = openai_call.kwargs["json"]
        system_msg = next(m["content"] for m in openai_payload["messages"] if m["role"] == "system")
        assert "ACTIVE RETINAGUARD SCAN CONTEXT" in system_msg
        assert "Mild Non-Proliferative DR" in system_msg
