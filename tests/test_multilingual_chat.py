"""Backend tests for Task 23: Multilingual MedAssist & Universal Language Support."""

from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.chat import ChatMessage, ChatRequest, ScanContext
from app.services.chat_service import (
    _build_complete_system_prompt,
    _build_language_instruction,
    LANGUAGE_NAMES,
)

client = TestClient(app)


def _mock_gemini_reply(reply_text: str = "Grounded educational response.") -> httpx.Response:
    return httpx.Response(
        status_code=200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": reply_text}]
                    },
                    "finishReason": "STOP",
                }
            ]
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )


class TestMultilingualChatRequestSchema:
    """Verifies ChatRequest schema validation, defaults, and sanitization for language preference."""

    def test_default_language_is_en(self):
        req = ChatRequest(message="Explain mild diabetic retinopathy")
        assert req.language == "en"

    def test_valid_language_codes_accepted_and_sanitized(self):
        for code in ["ta", "hi", "te", "en", "EN", "hi-IN", "ta-IN"]:
            req = ChatRequest(message="Test query", language=code)
            assert req.language == code.strip().lower()

    def test_blank_or_none_language_defaults_to_en(self):
        req = ChatRequest(message="Test query", language="")
        assert req.language == "en"

    def test_invalid_language_code_rejected_with_validation_error(self):
        with pytest.raises(Exception):
            ChatRequest(message="Test query", language="toolonglanguagenameexceedinglimit")

        with pytest.raises(Exception):
            ChatRequest(message="Test query", language="ta;DROP TABLE;")


class TestLanguageDirectivePromptBuilder:
    """Verifies that _build_language_instruction injects appropriate safety and terminology guidance."""

    def test_english_produces_no_extra_directive(self):
        assert _build_language_instruction("en") == ""
        assert _build_language_instruction("en-US") == ""
        assert _build_language_instruction(None) == ""

    def test_supported_languages_produce_clear_directives(self):
        for lang_code, lang_name in [("ta", "Tamil"), ("hi", "Hindi"), ("te", "Telugu")]:
            directive = _build_language_instruction(lang_code)
            assert "LANGUAGE DIRECTIVE" in directive
            assert lang_name in directive
            assert "accessible words" in directive
            assert "clinical English medical terms in parentheses" in directive
            assert "preserve all non-diagnostic safety disclaimers" in directive

    def test_system_prompt_enrichment_preserves_safety_and_scan_context(self):
        scan_ctx = ScanContext(
            modality="retina",
            predicted_class=1,
            class_label="Mild Non-Proliferative DR",
            confidence_score=0.88,
            model_version="ResNet-18",
            session_id="00000000-0000-0000-0000-000000000001",
        )
        prompt_ta = _build_complete_system_prompt(scan_ctx, language="ta")
        assert "LANGUAGE DIRECTIVE" in prompt_ta
        assert "Tamil" in prompt_ta
        assert "CRITICAL MEDICAL SAFETY & ETHICAL RULES" in prompt_ta
        assert "ACTIVE RETINAGUARD SCAN CONTEXT" in prompt_ta
        assert "Mild Non-Proliferative DR" in prompt_ta


class TestMultilingualChatEndpoint:
    """Verifies the HTTP endpoint /api/v1/chat/message with language preferences."""

    def test_chat_message_with_language_parameter(self, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-valid-key-12345")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        mock_resp = _mock_gemini_reply(
            "விழித்திரை பாதிப்பு (Diabetic Retinopathy) என்பது சர்க்கரை நோயினால் கண்களில் ஏற்படும் மாற்றமாகும்."
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            payload = {
                "message": "விழித்திரை பாதிப்பு என்றால் என்ன?",
                "conversation_history": [],
                "language": "ta",
            }
            resp = client.post("/api/v1/chat/message", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert "message" in data
            assert "விழித்திரை" in data["message"]
            assert data["provider"] == "gemini"
            assert "EDUCATIONAL RESEARCH USE ONLY" in data["disclaimer"]

    def test_backward_compatibility_without_language_field(self, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-valid-key-12345")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        mock_resp = _mock_gemini_reply("Standard English educational reply.")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            # Legacy payload lacking language field
            payload = {
                "message": "What is diabetic retinopathy?",
                "conversation_history": [],
            }
            resp = client.post("/api/v1/chat/message", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["message"] == "Standard English educational reply."
