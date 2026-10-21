"""Regression tests for RetinaGuard checkpoint selection, fallback, overrides, and status reporting."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.retina_service import (
    RetinaModelService,
    determine_model_version_and_metadata,
    get_retina_service,
    reset_retina_service,
    resolve_retina_checkpoint,
)


@pytest.fixture(autouse=True)
def restore_retina_service():
    """Ensure global singleton is cleanly restored after each test."""
    yield
    reset_retina_service(None)


def test_v2_selected_when_both_checkpoints_exist():
    """Verify retinaguard_v2.pt is preferred when both V2 and baseline exist."""
    root = settings.PROJECT_ROOT
    v2_expected = (root / "ai_models" / "retina" / "weights" / "retinaguard_v2.pt").resolve()
    baseline_expected = (root / "ai_models" / "retina" / "weights" / "best_model.pt").resolve()

    assert v2_expected.is_file(), "retinaguard_v2.pt must exist for this test"
    assert baseline_expected.is_file(), "best_model.pt must exist for this test"

    resolved_path, source, error = resolve_retina_checkpoint(
        override_path=None,
        allow_fallback=True,
        project_root=root,
    )

    assert error is None
    assert source == "v2_preferred"
    assert resolved_path == v2_expected


def test_fallback_to_baseline_when_v2_absent(tmp_path):
    """Verify best_model.pt is used only as fallback when V2 is absent and fallback is allowed."""
    # Create a mock tree with only best_model.pt
    mock_weights_dir = tmp_path / "ai_models" / "retina" / "weights"
    mock_weights_dir.mkdir(parents=True, exist_ok=True)
    mock_baseline = mock_weights_dir / "best_model.pt"
    mock_baseline.write_text("mock baseline")

    # When fallback is allowed
    resolved_path, source, error = resolve_retina_checkpoint(
        override_path=None,
        allow_fallback=True,
        project_root=tmp_path,
    )
    assert error is None
    assert source == "baseline_fallback"
    assert resolved_path == mock_baseline.resolve()

    # When fallback is disabled
    resolved_no_fallback, source_no_fallback, error_no_fallback = resolve_retina_checkpoint(
        override_path=None,
        allow_fallback=False,
        project_root=tmp_path,
    )
    assert resolved_no_fallback is None
    assert source_no_fallback == "none"
    assert "No valid RetinaGuard checkpoint found" in error_no_fallback


def test_user_configured_override_handled_correctly(tmp_path):
    """Verify configured checkpoint override is respected when valid."""
    mock_weights_dir = tmp_path / "ai_models" / "retina" / "weights"
    mock_weights_dir.mkdir(parents=True, exist_ok=True)
    (mock_weights_dir / "retinaguard_v2.pt").write_text("v2")
    custom_ckpt = mock_weights_dir / "custom_checkpoint.pt"
    custom_ckpt.write_text("custom")

    # Relative override path
    resolved_rel, source_rel, error_rel = resolve_retina_checkpoint(
        override_path="ai_models/retina/weights/custom_checkpoint.pt",
        project_root=tmp_path,
    )
    assert error_rel is None
    assert source_rel == "override"
    assert resolved_rel == custom_ckpt.resolve()

    # Absolute override path
    resolved_abs, source_abs, error_abs = resolve_retina_checkpoint(
        override_path=str(custom_ckpt.resolve()),
        project_root=tmp_path,
    )
    assert error_abs is None
    assert source_abs == "override"
    assert resolved_abs == custom_ckpt.resolve()


def test_user_configured_override_invalid_does_not_silently_fallback(tmp_path):
    """Verify invalid override produces clear error and does NOT silently fall back to V2 or baseline."""
    mock_weights_dir = tmp_path / "ai_models" / "retina" / "weights"
    mock_weights_dir.mkdir(parents=True, exist_ok=True)
    (mock_weights_dir / "retinaguard_v2.pt").write_text("v2")
    (mock_weights_dir / "best_model.pt").write_text("baseline")

    resolved, source, error = resolve_retina_checkpoint(
        override_path="ai_models/retina/weights/nonexistent.pt",
        allow_fallback=True,
        project_root=tmp_path,
    )
    assert resolved is None
    assert source == "override_invalid"
    assert "override not found" in error


def test_missing_all_checkpoints_produces_clear_readiness_error(tmp_path):
    """Verify missing checkpoints result in unloaded service with descriptive readiness error."""
    service = RetinaModelService(project_root=tmp_path)

    assert service.is_loaded is False
    assert service.model_version == "unloaded"
    assert service.checkpoint_path is None
    assert service.checkpoint_filename is None
    assert "No valid RetinaGuard checkpoint found" in service.status_message

    # predict() must raise RuntimeError explaining model is not loaded
    with pytest.raises(RuntimeError, match="RetinaGuard model is not loaded"):
        service.predict(b"dummy")


def test_model_version_trustworthy_determination():
    """Verify version is retinaguard_v2_epoch8 ONLY when confirmed as V2 Epoch 8."""
    # V2 Epoch 8 -> exactly retinaguard_v2_epoch8
    ver, epoch, f1 = determine_model_version_and_metadata(
        Path("ai_models/retina/weights/retinaguard_v2.pt"),
        {"epoch": 8, "val_macro_f1": 0.6931},
    )
    assert ver == "retinaguard_v2_epoch8"
    assert epoch == 8
    assert f1 == 0.6931

    # V2 Epoch 2 (e.g. earlier training checkpoint) -> must not claim epoch8
    ver2, epoch2, _ = determine_model_version_and_metadata(
        Path("ai_models/retina/weights/retinaguard_v2_epoch2.pt"),
        {"epoch": 2, "val_macro_f1": 0.5616},
    )
    assert ver2 == "retinaguard_v2_epoch2"
    assert epoch2 == 2

    # Baseline Epoch 1 -> must reflect baseline, not V2
    ver_base, epoch_base, _ = determine_model_version_and_metadata(
        Path("ai_models/retina/weights/best_model.pt"),
        {"epoch": 1, "val_macro_f1": 0.1317},
    )
    assert ver_base == "retinaguard_baseline_epoch1"
    assert epoch_base == 1

    # Custom override checkpoint with epoch
    ver_custom, epoch_custom, _ = determine_model_version_and_metadata(
        Path("custom_model.pt"),
        {"epoch": 5},
    )
    assert ver_custom == "retina_resnet18_epoch5"
    assert epoch_custom == 5

    # Checkpoint without epoch metadata -> fallback to config
    ver_fallback, _, _ = determine_model_version_and_metadata(
        Path("legacy.pt"),
        {"config": {"model_version": "retina_custom_v1"}},
    )
    assert ver_fallback == "retina_custom_v1"


def test_api_status_endpoint_reflects_actual_loaded_v2_checkpoint(client: TestClient):
    """Verify GET /api/v1/retina/model-status returns trustworthy V2 Epoch 8 metadata."""
    reset_retina_service(None)
    response = client.get("/api/v1/retina/model-status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["is_loaded"] is True
    assert data["model_version"] == "retinaguard_v2_epoch8"
    assert data["checkpoint_filename"] == "retinaguard_v2.pt"
    assert data["checkpoint_epoch"] == 8
    assert data["checkpoint_val_macro_f1"] == 0.6931
    assert data["selection_source"] == "v2_preferred"
    assert data["checkpoint_path"].endswith("retinaguard_v2.pt")
    assert "retinaguard_v2.pt" in data["status_message"]


def test_api_predict_returns_503_when_service_unloaded(client: TestClient, create_sample_image, tmp_path):
    """Verify POST /api/v1/retina/predict returns HTTP 503 when model cannot be loaded."""
    unloaded_service = RetinaModelService(project_root=tmp_path)
    reset_retina_service(unloaded_service)

    img_bytes = create_sample_image(format="JPEG", size=(224, 224))
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/v1/retina/predict", files=files)
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_live_inference_on_existing_validation_image(client: TestClient):
    """Verify full end-to-end inference on an authentic APTOS validation image using V2 checkpoint."""
    reset_retina_service(None)
    val_img = Path("datasets/aptos/train_images/99c626e58464.png")
    assert val_img.is_file(), f"Validation image {val_img} must exist."

    with open(val_img, "rb") as f:
        files = {"file": ("val_99c626e58464.png", f.read(), "image/png")}

    response = client.post("/api/v1/retina/predict?include_gradcam=true", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["modality"] == "retina"
    assert data["model_version"] == "retinaguard_v2_epoch8"

    pred = data["prediction"]
    assert 0 <= pred["predicted_class"] <= 4
    assert pred["severity_level"] in ["None", "Mild", "Moderate", "Severe", "Proliferative"]
    assert 0.0 <= pred["confidence_score"] <= 1.0
    assert len(pred["all_class_scores"]) == 5
    score_sum = sum(pred["all_class_scores"].values())
    assert 0.99 <= score_sum <= 1.01
    assert "uncalibrated" in pred["calibration_notice"].lower()

    # Visual explainability
    expl = data["explanation"]
    assert expl is not None
    assert expl["heatmap_overlay_base64"].startswith("data:image/png;base64,")
    assert expl["raw_heatmap_base64"].startswith("data:image/png;base64,")
    assert "attention" in expl["interpretability_note"].lower()

    # Mandatory medical disclaimer
    assert "RESEARCH PROTOTYPE ONLY" in data["disclaimer"]
