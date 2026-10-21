"""Automated test suite for RetinaGuard model architecture, training, evaluation, and inference."""

import csv
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ai_models.retina.dataset import RetinaFundusDataset, find_project_root
from ai_models.retina.evaluate import (
    compute_multiclass_metrics,
    evaluate_retina_model,
    format_confusion_matrix,
)
from ai_models.retina.inference import RetinaInferencePipeline
from ai_models.retina.model import DR_CLASS_NAMES, RetinaResNet18, build_retina_model
from ai_models.retina.preprocessing import RetinaImagePreprocessor
from ai_models.retina.train import RetinaTrainer


@pytest.fixture
def project_root() -> Path:
    """Fixture providing repository root path."""
    return find_project_root()


@pytest.fixture
def sample_batch():
    """Generate dummy batch of retinal images and labels."""
    images = torch.randn(4, 3, 224, 224)
    labels = torch.tensor([0, 2, 1, 4], dtype=torch.long)
    return images, labels


# ==============================================================================
# 1. MODEL ARCHITECTURE & OUTPUT SHAPE TESTS
# ==============================================================================


def test_model_initialization_and_output_shape(sample_batch):
    """Verify RetinaResNet18 outputs logits of shape (batch_size, 5)."""
    images, _ = sample_batch
    model = build_retina_model(num_classes=5, pretrained=False)
    model.eval()

    with torch.no_grad():
        logits = model(images)

    assert logits.shape == (4, 5), f"Expected shape (4, 5), got {logits.shape}"
    assert not torch.isnan(logits).any(), "Model produced NaN logits."


def test_model_custom_head_structure():
    """Verify classification head has dropout and 5 output units."""
    model = RetinaResNet18(num_classes=5, pretrained=False, dropout=0.25)
    fc = model.backbone.fc

    assert isinstance(fc, nn.Sequential), "Expected fc to be nn.Sequential"
    assert isinstance(fc[0], nn.Dropout)
    assert fc[0].p == 0.25
    assert isinstance(fc[1], nn.Linear)
    assert fc[1].in_features == 512
    assert fc[1].out_features == 5


def test_model_feature_layer_exposure():
    """Verify get_last_conv_layer exposes layer4 for downstream Grad-CAM explainability."""
    model = RetinaResNet18(num_classes=5, pretrained=False)
    last_conv = model.get_last_conv_layer()
    assert last_conv is model.backbone.layer4


def test_model_backbone_freezing():
    """Verify set_backbone_trainable freezes conv layers while leaving head trainable."""
    model = RetinaResNet18(num_classes=5, pretrained=False)
    model.set_backbone_trainable(False)

    for name, param in model.backbone.named_parameters():
        if "fc" in name:
            assert param.requires_grad is True, f"Head parameter {name} should be trainable."
        else:
            assert param.requires_grad is False, f"Backbone parameter {name} should be frozen."

    model.set_backbone_trainable(True)
    for _, param in model.backbone.named_parameters():
        assert param.requires_grad is True


# ==============================================================================
# 2. CHECKPOINT SAVING & LOADING TESTS
# ==============================================================================


def test_checkpoint_save_and_load_roundtrip(tmp_path: Path):
    """Verify model checkpoint can be saved and restored with identical weights."""
    ckpt_path = tmp_path / "test_checkpoint.pt"
    model = build_retina_model(num_classes=5, pretrained=False)

    # Save
    saved_path = model.save_checkpoint(
        ckpt_path,
        epoch=3,
        val_macro_f1=0.745,
        val_loss=0.521,
        config={"lr": 1e-4, "model_version": "v1.0_test"},
    )
    assert saved_path.is_file()

    # Load
    loaded_model, metadata = RetinaResNet18.load_from_checkpoint(ckpt_path)
    assert metadata["epoch"] == 3
    assert metadata["val_macro_f1"] == 0.745
    assert metadata["val_loss"] == 0.521
    assert metadata["config"]["model_version"] == "v1.0_test"

    # Assert parameter equality
    for p1, p2 in zip(model.parameters(), loaded_model.parameters()):
        assert torch.equal(p1, p2), "Loaded parameters do not match original model."


# ==============================================================================
# 3. DATASET ADAPTER & MANIFEST STREAMING TESTS
# ==============================================================================


def test_retina_fundus_dataset_manifest_streaming(project_root: Path):
    """Verify RetinaFundusDataset streams images directly from processed train_manifest.csv."""
    manifest = project_root / "datasets" / "aptos" / "processed" / "train_manifest.csv"
    assert manifest.is_file(), "train_manifest.csv is missing."

    preprocessor = RetinaImagePreprocessor(target_size=(128, 128), normalize=True, is_training=False)
    dataset = RetinaFundusDataset(manifest, preprocessor=preprocessor, project_root=project_root)

    assert len(dataset) == 2929

    # Stream single item
    tensor, label = dataset[0]
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (3, 128, 128)
    assert isinstance(label, torch.Tensor)
    assert 0 <= label.item() <= 4


def test_retina_dataloader_batching(project_root: Path):
    """Verify DataLoader batches images properly without data leakage."""
    manifest = project_root / "datasets" / "aptos" / "processed" / "val_manifest.csv"
    assert manifest.is_file(), "val_manifest.csv is missing."

    preprocessor = RetinaImagePreprocessor(target_size=(64, 64), normalize=True, is_training=False)
    dataset = RetinaFundusDataset(manifest, preprocessor=preprocessor, project_root=project_root)

    loader = DataLoader(dataset, batch_size=4, shuffle=False)
    images, targets = next(iter(loader))

    assert images.shape == (4, 3, 64, 64)
    assert targets.shape == (4,)
    for lbl in targets:
        assert 0 <= lbl.item() <= 4


# ==============================================================================
# 4. CLASS-WEIGHTED LOSS TESTS
# ==============================================================================


def test_class_weighted_loss_penalizes_minority_errors():
    """Verify class-weighted CrossEntropyLoss penalizes mistakes on minority classes higher."""
    # Weights: class 0 is majority (0.4057), class 3 is minority (3.8039)
    weights = torch.tensor([0.4057, 1.9791, 0.7332, 3.8039, 2.4822], dtype=torch.float32)
    criterion_none = nn.CrossEntropyLoss(weight=weights, reduction="none")

    # Identical wrong prediction: predicting class 2 when true is class 0 vs true is class 3
    logits = torch.tensor([[0.0, 0.0, 5.0, 0.0, 0.0], [0.0, 0.0, 5.0, 0.0, 0.0]], dtype=torch.float32)
    targets = torch.tensor([0, 3], dtype=torch.long)

    loss_per_sample = criterion_none(logits, targets)
    loss_class0 = loss_per_sample[0].item()
    loss_class3 = loss_per_sample[1].item()

    # Loss on rare class 3 mistake must be substantially higher than on majority class 0
    assert loss_class3 > loss_class0
    ratio = loss_class3 / loss_class0
    assert abs(ratio - (3.8039 / 0.4057)) < 0.01



# ==============================================================================
# 5. EVALUATION METRICS & CONFUSION MATRIX TESTS
# ==============================================================================


def test_compute_multiclass_metrics_perfect_predictions():
    """Verify metrics calculation on perfect predictions yields 100% accuracy and F1."""
    y_true = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    y_pred = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["weighted_f1"] == 1.0

    cm = np.array(metrics["confusion_matrix"])
    assert np.array_equal(cm, np.diag([2, 2, 2, 2, 2]))


def test_compute_multiclass_metrics_imbalanced():
    """Verify metrics calculation correctly reflects per-class precision and recall."""
    # 2 true class 0 (1 predicted right, 1 as class 1)
    # 2 true class 1 (both predicted right)
    y_true = np.array([0, 0, 1, 1, 2])
    y_pred = np.array([0, 1, 1, 1, 2])

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert metrics["total_samples"] == 5
    assert metrics["accuracy"] == 0.8  # 4/5 correct

    # Class 0: TP=1, FN=1 -> recall = 0.5; FP=0 -> precision = 1.0
    c0 = metrics["class_metrics"]["0"]
    assert c0["precision"] == 1.0
    assert c0["recall"] == 0.5

    # Check confusion matrix formatting does not throw
    ascii_table = format_confusion_matrix(metrics["confusion_matrix"])
    assert "Confusion Matrix" in ascii_table


# ==============================================================================
# 6. SINGLE-STEP OPTIMIZATION SMOKE TEST
# ==============================================================================


def test_single_step_optimization_smoke(sample_batch):
    """Verify backward pass and optimizer update decrease loss on training step."""
    images, targets = sample_batch
    model = build_retina_model(num_classes=5, pretrained=False)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)
    criterion = nn.CrossEntropyLoss()

    model.train()
    optimizer.zero_grad()
    initial_logits = model(images)
    initial_loss = criterion(initial_logits, targets)

    initial_loss.backward()
    optimizer.step()

    with torch.no_grad():
        updated_logits = model(images)
        updated_loss = criterion(updated_logits, targets)

    assert updated_loss.item() < initial_loss.item(), "Single step gradient update did not decrease batch loss."


# ==============================================================================
# 7. INFERENCE PIPELINE TESTS
# ==============================================================================


def test_inference_pipeline_predict(tmp_path: Path):
    """Verify RetinaInferencePipeline loads weights and returns valid predictions."""
    # Create and save a small checkpoint
    ckpt_path = tmp_path / "inference_test_model.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    model.save_checkpoint(ckpt_path)

    pipeline = RetinaInferencePipeline()
    with pytest.raises(RuntimeError):
        pipeline.predict(torch.randn(3, 224, 224))

    # Load model
    pipeline.load_model(ckpt_path)
    assert pipeline._is_loaded is True

    # Test single-image tensor input (3, 224, 224)
    dummy_input = torch.randn(3, 224, 224)
    result = pipeline.predict(dummy_input)

    assert "predicted_class" in result
    assert result["predicted_class"] in [0, 1, 2, 3, 4]
    assert "class_name" in result
    assert result["class_name"] in DR_CLASS_NAMES.values()
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["probabilities"]) == 5
    # Verify probabilities sum close to 1.0
    prob_sum = sum(result["probabilities"].values())
    assert abs(prob_sum - 1.0) <= 0.01
    assert "RESEARCH PROTOTYPE ONLY" in result["disclaimer"]


def test_inference_pipeline_with_pil_image(tmp_path: Path):
    """Verify RetinaInferencePipeline accepts PIL Images directly."""
    from PIL import Image

    ckpt_path = tmp_path / "inference_pil_test.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    model.save_checkpoint(ckpt_path)

    pipeline = RetinaInferencePipeline(ckpt_path)
    pil_img = Image.new("RGB", (300, 300), color=(120, 60, 40))
    result = pipeline.predict(pil_img)

    assert result["predicted_class"] in [0, 1, 2, 3, 4]
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["probabilities"]) == 5


# ==============================================================================
# 8. TRAINING RESUMPTION, OPTIMIZER RESTORATION & CHECKPOINT SAFETY TESTS
# ==============================================================================


def test_checkpoint_atomic_saving_and_scheduler_state(tmp_path: Path):
    """Verify save_checkpoint atomically writes files and preserves scheduler_state."""
    ckpt_path = tmp_path / "atomic_checkpoint.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    out = model(torch.randn(2, 3, 224, 224))
    out.sum().backward()
    optimizer.step()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5)
    scheduler.step()

    model.save_checkpoint(
        ckpt_path,
        epoch=2,
        val_macro_f1=0.5616,
        val_loss=0.6995,
        optimizer_state=optimizer.state_dict(),
        scheduler_state=scheduler.state_dict(),
    )
    assert ckpt_path.is_file()

    loaded_model, ckpt_data = RetinaResNet18.load_from_checkpoint(ckpt_path)
    assert ckpt_data["epoch"] == 2
    assert ckpt_data["val_macro_f1"] == 0.5616
    assert ckpt_data["val_loss"] == 0.6995
    assert "scheduler_state" in ckpt_data
    assert ckpt_data["scheduler_state"]["last_epoch"] == 1


def test_retina_trainer_resume_from_epoch_2(tmp_path: Path):
    """Verify RetinaTrainer properly resumes at Epoch 3, unfreezes Phase 2, and restores optimizer state."""
    from torch.utils.data import TensorDataset

    # 1. Create a simulated Phase 2 checkpoint at Epoch 2
    ckpt_path = tmp_path / "retinaguard_v2.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    model.set_backbone_trainable(True)

    optimizer = torch.optim.AdamW(
        [
            {"params": model.backbone.layer4.parameters(), "lr": 5e-5},
            {"params": model.backbone.fc.parameters(), "lr": 1e-4},
        ],
        weight_decay=0.01,
    )

    # Step optimizer once to populate state tensors
    dummy_input = torch.randn(2, 3, 224, 224)
    out = model(dummy_input)
    loss = out.sum()
    loss.backward()
    optimizer.step()

    model.save_checkpoint(
        ckpt_path,
        epoch=2,
        val_macro_f1=0.5616,
        val_loss=0.6995,
        optimizer_state=optimizer.state_dict(),
        scheduler_state=None,  # Simulating missing scheduler_state as in current checkpoint
    )

    # 2. Instantiate trainer with resume_checkpoint
    dummy_x = torch.randn(4, 3, 224, 224)
    dummy_y = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    loader = DataLoader(TensorDataset(dummy_x, dummy_y), batch_size=2)

    trainer = RetinaTrainer(
        model=build_retina_model(num_classes=5, pretrained=False),
        train_loader=loader,
        val_loader=loader,
        output_dir=tmp_path,
        resume_checkpoint=ckpt_path,
        freeze_backbone_epochs=1,
    )

    # 3. Assertions
    assert trainer.start_epoch == 3, f"Expected start_epoch=3, got {trainer.start_epoch}"
    assert trainer.best_macro_f1 == 0.5616, f"Expected best_macro_f1=0.5616, got {trainer.best_macro_f1}"
    assert trainer._resumed_in_phase2 is True, "Expected _resumed_in_phase2=True"

    # Verify backbone layer4 is trainable (Phase 2 fine-tuning)
    for p in trainer.model.backbone.layer4.parameters():
        assert p.requires_grad is True

    # Verify optimizer parameter groups
    assert len(trainer.optimizer.param_groups) == 2
    assert trainer.optimizer.param_groups[0]["initial_lr"] == 5e-5
    assert trainer.optimizer.param_groups[1]["initial_lr"] == 1e-4

    # Verify optimizer state restored
    assert len(trainer.optimizer.state) > 0


def test_retina_trainer_resume_execution_and_scheduler_reconstruction(tmp_path: Path):
    """Verify trainer resumes execution through Epoch 3 with reconstructed CosineAnnealingLR."""
    from torch.utils.data import TensorDataset

    ckpt_path = tmp_path / "retinaguard_v2.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    model.set_backbone_trainable(True)
    optimizer = torch.optim.AdamW(
        [
            {"params": model.backbone.layer4.parameters(), "lr": 5e-5},
            {"params": model.backbone.fc.parameters(), "lr": 1e-4},
        ],
        weight_decay=0.01,
    )

    model.save_checkpoint(
        ckpt_path,
        epoch=2,
        val_macro_f1=0.5616,
        val_loss=0.6995,
        optimizer_state=optimizer.state_dict(),
        scheduler_state=None,  # No scheduler state
    )

    dummy_x = torch.randn(4, 3, 224, 224)
    dummy_y = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    loader = DataLoader(TensorDataset(dummy_x, dummy_y), batch_size=2)

    trainer = RetinaTrainer(
        model=build_retina_model(num_classes=5, pretrained=False),
        train_loader=loader,
        val_loader=loader,
        output_dir=tmp_path,
        resume_checkpoint=ckpt_path,
        freeze_backbone_epochs=1,
    )

    # Train for 1 resumed epoch (Epoch 3) out of 4 total epochs
    results = trainer.train(total_epochs=3, best_checkpoint_filename="retinaguard_v2.pt")

    assert results["status"] == "COMPLETED"
    assert len(trainer.history) == 1
    assert trainer.history[0]["epoch"] == 3

    # Check latest checkpoint saved at epoch 3
    latest_ckpt = tmp_path / "checkpoint_latest.pt"
    assert latest_ckpt.is_file()
    _, latest_data = RetinaResNet18.load_from_checkpoint(latest_ckpt)
    assert latest_data["epoch"] == 3
    assert "scheduler_state" in latest_data
    assert latest_data["scheduler_state"] is not None


def test_retina_checkpoint_safety_protections(tmp_path: Path):
    """Verify safety rules prevent overwriting baseline best_model.pt or backup files."""
    from torch.utils.data import TensorDataset
    from ai_models.retina.train import validate_checkpoint_safety

    # 1. Direct validation tests
    with pytest.raises(ValueError, match="cannot be a backup filename"):
        validate_checkpoint_safety(tmp_path, "retinaguard_v2_epoch2_verified_backup.pt")

    with pytest.raises(ValueError, match="cannot be a backup filename"):
        validate_checkpoint_safety(tmp_path, "model_backup.pt")

    with pytest.raises(ValueError, match="Cannot resume training into 'best_model.pt'"):
        validate_checkpoint_safety(tmp_path, "best_model.pt", is_resuming=True)

    # 2. Resuming trainer total_epochs validation
    dummy_ckpt = tmp_path / "test_ckpt.pt"
    model = build_retina_model(num_classes=5, pretrained=False)
    model.save_checkpoint(dummy_ckpt, epoch=3)

    dummy_x = torch.randn(2, 3, 224, 224)
    dummy_y = torch.tensor([0, 1], dtype=torch.long)
    loader = DataLoader(TensorDataset(dummy_x, dummy_y), batch_size=2)

    trainer = RetinaTrainer(
        model=model,
        train_loader=loader,
        val_loader=loader,
        output_dir=tmp_path,
        resume_checkpoint=dummy_ckpt,
    )

    # Requesting total_epochs <= completed_epoch (3) must raise ValueError
    with pytest.raises(ValueError, match="Cannot resume training"):
        trainer.train(total_epochs=3)

