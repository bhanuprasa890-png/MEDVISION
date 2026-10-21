"""Automated test suite for RetinaGuard evaluation pipeline.

Tests:
1. Multi-class metric calculations: accuracy, precision, recall, F1, macro/weighted F1.
2. Safe handling of edge cases: empty datasets, missing classes, zero-predicted classes, class collapse.
3. Diabetic Retinopathy 5-class mapping verification.
4. Confusion matrix formatting (ASCII and Markdown).
5. Data leakage detection across dataset manifests.
6. Checkpoint loading error handling (non-existent, corrupted).
7. Invariance of model weights and inference behavior during evaluation.
8. Markdown and JSON report generation integrity.
"""

import io
import json
from pathlib import Path
import numpy as np
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ai_models.retina.evaluate import (
    check_data_leakage,
    compute_multiclass_metrics,
    evaluate_retina_model,
    format_confusion_matrix,
    format_markdown_confusion_matrix,
    generate_markdown_report,
    run_evaluation,
)
from ai_models.retina.model import DR_CLASS_NAMES, RetinaResNet18, build_retina_model


# ==============================================================================
# 1. METRIC CALCULATION TESTS
# ==============================================================================


def test_compute_multiclass_metrics_perfect():
    """Verify metrics calculation on perfect predictions yields 100% accuracy and F1."""
    y_true = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert metrics["total_samples"] == 10
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["weighted_f1"] == 1.0
    assert len(metrics["zero_prediction_classes"]) == 0
    assert len(metrics["zero_support_classes"]) == 0

    for c in range(5):
        c_meta = metrics["class_metrics"][str(c)]
        assert c_meta["precision"] == 1.0
        assert c_meta["recall"] == 1.0
        assert c_meta["f1_score"] == 1.0
        assert c_meta["support"] == 2
        assert c_meta["predicted_count"] == 2


def test_compute_multiclass_metrics_empty_dataset():
    """Verify empty input array returns safe zero metrics without throwing exceptions."""
    metrics = compute_multiclass_metrics([], [], num_classes=5)
    assert metrics["total_samples"] == 0
    assert metrics["accuracy"] == 0.0
    assert metrics["macro_f1"] == 0.0
    assert metrics["weighted_f1"] == 0.0
    assert len(metrics["class_metrics"]) == 5
    assert len(metrics["zero_prediction_classes"]) == 5
    assert len(metrics["zero_support_classes"]) == 5
    for c in range(5):
        assert metrics["class_metrics"][str(c)]["support"] == 0
        assert metrics["class_metrics"][str(c)]["f1_score"] == 0.0


def test_compute_multiclass_metrics_missing_classes():
    """Verify missing classes in ground truth (zero support) are handled safely."""
    # Only classes 0 and 1 are present; classes 2, 3, 4 have 0 support
    y_true = [0, 0, 1, 1]
    y_pred = [0, 0, 1, 1]

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert metrics["total_samples"] == 4
    assert metrics["accuracy"] == 1.0
    # Classes 2, 3, 4 have support=0 and precision=0, recall=0, f1=0
    assert set(metrics["zero_support_classes"]) == {2, 3, 4}
    assert metrics["class_metrics"]["0"]["f1_score"] == 1.0
    assert metrics["class_metrics"]["1"]["f1_score"] == 1.0
    assert metrics["class_metrics"]["2"]["f1_score"] == 0.0
    # Macro F1 is average over all 5 classes: (1.0 + 1.0 + 0 + 0 + 0) / 5 = 0.4
    assert round(metrics["macro_f1"], 2) == 0.40
    # Weighted F1 accounts only for classes with support: (1.0*2 + 1.0*2) / 4 = 1.0
    assert metrics["weighted_f1"] == 1.0


def test_compute_multiclass_metrics_zero_predictions():
    """Verify classes with zero predictions handle division by zero safely without errors."""
    # Class 3 is never predicted (y_pred has no 3)
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 2, 4]  # class 3 is mispredicted as class 2

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert 3 in metrics["zero_prediction_classes"]
    c3 = metrics["class_metrics"]["3"]
    assert c3["predicted_count"] == 0
    assert c3["tp"] == 0
    assert c3["precision"] == 0.0
    assert c3["recall"] == 0.0
    assert c3["f1_score"] == 0.0


def test_compute_multiclass_metrics_class_collapse():
    """Verify extreme scenario where all samples are predicted as Class 0."""
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 0, 0, 0, 0]

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    assert metrics["total_samples"] == 5
    assert metrics["accuracy"] == 0.20  # 1 out of 5
    assert set(metrics["zero_prediction_classes"]) == {1, 2, 3, 4}

    # Class 0: TP=1, FP=4 -> precision = 1/5 = 0.20, recall = 1/1 = 1.0
    c0 = metrics["class_metrics"]["0"]
    assert c0["precision"] == 0.20
    assert c0["recall"] == 1.0
    assert round(c0["f1_score"], 4) == round(2 * 0.2 * 1.0 / (0.2 + 1.0), 4)


# ==============================================================================
# 2. CLASS MAPPING INTEGRITY
# ==============================================================================


def test_dr_class_mapping_integrity():
    """Verify the 5 output classes map strictly to the APTOS clinical definitions."""
    expected_mapping = {
        0: "No Diabetic Retinopathy",
        1: "Mild Non-Proliferative DR",
        2: "Moderate Non-Proliferative DR",
        3: "Severe Non-Proliferative DR",
        4: "Proliferative Diabetic Retinopathy",
    }
    assert len(DR_CLASS_NAMES) == 5
    for class_id, expected_name in expected_mapping.items():
        assert DR_CLASS_NAMES[class_id] == expected_name


# ==============================================================================
# 3. CONFUSION MATRIX FORMATTING
# ==============================================================================


def test_format_confusion_matrix_ascii():
    """Verify ASCII confusion matrix contains all rows, columns, and headers."""
    cm = [
        [10, 2, 0, 0, 0],
        [1, 8, 1, 0, 0],
        [0, 2, 7, 1, 0],
        [0, 0, 1, 5, 1],
        [0, 0, 0, 1, 4],
    ]
    formatted = format_confusion_matrix(cm, num_classes=5)
    assert "Confusion Matrix" in formatted
    assert "True \\ Pred | C0 | C1 | C2 | C3 | C4" in formatted
    assert "Class 0" in formatted
    assert "Class 4" in formatted


def test_format_confusion_matrix_markdown():
    """Verify Markdown confusion matrix generates valid GitHub markdown table syntax."""
    cm = [
        [5, 1, 0, 0, 0],
        [0, 4, 0, 0, 0],
        [0, 0, 3, 0, 0],
        [0, 0, 0, 2, 0],
        [0, 0, 0, 0, 1],
    ]
    md_table = format_markdown_confusion_matrix(cm, num_classes=5)
    assert "| True \\ Pred |" in md_table
    assert "| :--- |" in md_table
    assert "**True C0" in md_table
    assert "**5**" in md_table


# ==============================================================================
# 4. DATA LEAKAGE DETECTION
# ==============================================================================


def test_check_data_leakage_no_overlap(tmp_path):
    """Verify leakage check passes when train and eval manifests are strictly disjoint."""
    train_csv = tmp_path / "train.csv"
    train_csv.write_text("id_code,image_path,diagnosis\nimg1,path1,0\nimg2,path2,1\n", encoding="utf-8")

    eval_csv = tmp_path / "eval.csv"
    eval_csv.write_text("id_code,image_path,diagnosis\nimg3,path3,2\nimg4,path4,3\n", encoding="utf-8")

    leakage = check_data_leakage(eval_csv, train_csv, check_hashes=False)
    assert leakage["has_leakage"] is False
    assert leakage["id_overlap_count"] == 0
    assert len(leakage["id_overlap_samples"]) == 0


def test_check_data_leakage_detects_overlap(tmp_path):
    """Verify leakage check detects overlapping image IDs between splits."""
    train_csv = tmp_path / "train.csv"
    train_csv.write_text("id_code,image_path,diagnosis\nimg1,path1,0\nimg2,path2,1\n", encoding="utf-8")

    eval_csv = tmp_path / "eval.csv"
    eval_csv.write_text("id_code,image_path,diagnosis\nimg2,path2,1\nimg3,path3,2\n", encoding="utf-8")

    leakage = check_data_leakage(eval_csv, train_csv, check_hashes=False)
    assert leakage["has_leakage"] is True
    assert leakage["id_overlap_count"] == 1
    assert "img2" in leakage["id_overlap_samples"]


# ==============================================================================
# 5. CHECKPOINT LOADING ERROR HANDLING
# ==============================================================================


def test_checkpoint_loading_failure_nonexistent(tmp_path):
    """Verify attempting to load a non-existent checkpoint raises FileNotFoundError."""
    missing_file = tmp_path / "does_not_exist.pt"
    with pytest.raises(FileNotFoundError, match="Checkpoint not found"):
        RetinaResNet18.load_from_checkpoint(missing_file)


def test_checkpoint_loading_failure_corrupted(tmp_path):
    """Verify corrupted checkpoint file raises an exception safely."""
    corrupted_file = tmp_path / "corrupt.pt"
    corrupted_file.write_bytes(b"CorruptedPytorchHeaderBytes12345")

    with pytest.raises(Exception):
        RetinaResNet18.load_from_checkpoint(corrupted_file)


# ==============================================================================
# 6. NON-MODIFICATION OF MODEL WEIGHTS (EVALUATION SAFETY)
# ==============================================================================


def test_evaluation_does_not_modify_model_weights():
    """Verify that evaluate_retina_model does NOT mutate model parameters."""
    model = build_retina_model(num_classes=5, pretrained=False)

    # Clone initial parameter tensors
    initial_params = {name: param.clone() for name, param in model.named_parameters()}

    # Create dummy DataLoader
    dummy_images = torch.randn(8, 3, 224, 224)
    dummy_labels = torch.randint(0, 5, (8,))
    dataset = TensorDataset(dummy_images, dummy_labels)
    loader = DataLoader(dataset, batch_size=4)

    criterion = nn.CrossEntropyLoss()
    metrics = evaluate_retina_model(model, loader, criterion=criterion)

    assert metrics["total_samples"] == 8
    assert model.training is False

    # Verify every parameter tensor is byte-for-byte identical
    for name, param in model.named_parameters():
        assert torch.equal(param, initial_params[name]), f"Parameter {name} was modified during evaluation!"


# ==============================================================================
# 7. MARKDOWN REPORT GENERATION
# ==============================================================================


def test_generate_markdown_report_structure(tmp_path):
    """Verify Markdown report contains all required headers, tables, and disclaimers."""
    dummy_metrics = {
        "evaluated_at": "2026-10-17T12:00:00Z",
        "split_type": "validation",
        "is_independent_test_set": False,
        "manifest_evaluated": "val_manifest.csv",
        "checkpoint_evaluated": "best_model.pt",
        "checkpoint_epoch": 1,
        "total_samples": 100,
        "correct_count": 80,
        "accuracy": 0.80,
        "macro_f1": 0.75,
        "weighted_f1": 0.79,
        "val_loss": 0.6543,
        "class_metrics": {
            str(c): {
                "name": DR_CLASS_NAMES[c],
                "support": 20,
                "predicted_count": 20,
                "tp": 16,
                "fp": 4,
                "fn": 4,
                "precision": 0.80,
                "recall": 0.80,
                "f1_score": 0.80,
            }
            for c in range(5)
        },
        "confusion_matrix": [[16, 1, 1, 1, 1] for _ in range(5)],
        "leakage_assessment": {
            "train_manifest": "train_manifest.csv",
            "eval_manifest": "val_manifest.csv",
            "train_sample_count": 400,
            "eval_sample_count": 100,
            "id_overlap_count": 0,
        },
    }

    out_file = tmp_path / "test_report.md"
    md_content = generate_markdown_report(dummy_metrics, output_path=out_file)

    assert out_file.is_file()
    assert "# RetinaGuard — Model Evaluation Report" in md_content
    assert "Dataset Split Transparency Notice" in md_content
    assert "Global Performance Summary" in md_content
    assert "Per-Class Diagnostic Performance" in md_content
    assert "Multi-Class Confusion Matrix" in md_content
    assert "Medical Research Prototype Notice" in md_content
    assert "**80.00%**" in md_content


def test_generate_markdown_report_dynamic_class_counts(tmp_path):
    """Regression test ensuring narrative observation 1 derives class support counts dynamically."""
    # Test case 1: Real APTOS validation split counts (362, 73, 39)
    metrics_real_counts = {
        "evaluated_at": "2026-10-17T12:00:00Z",
        "split_type": "validation",
        "is_independent_test_set": False,
        "manifest_evaluated": "val_manifest.csv",
        "checkpoint_evaluated": "retinaguard_v2.pt",
        "checkpoint_epoch": 8,
        "total_samples": 733,
        "correct_count": 599,
        "accuracy": 0.8172,
        "macro_f1": 0.6931,
        "weighted_f1": 0.8186,
        "val_loss": 0.53,
        "class_metrics": {
            "0": {"name": "No Diabetic Retinopathy", "support": 362, "predicted_count": 359, "precision": 0.98, "recall": 0.97, "f1_score": 0.98},
            "1": {"name": "Mild Non-Proliferative DR", "support": 73, "predicted_count": 89, "precision": 0.57, "recall": 0.70, "f1_score": 0.63},
            "2": {"name": "Moderate Non-Proliferative DR", "support": 201, "predicted_count": 189, "precision": 0.74, "recall": 0.70, "f1_score": 0.72},
            "3": {"name": "Severe Non-Proliferative DR", "support": 39, "predicted_count": 46, "precision": 0.52, "recall": 0.62, "f1_score": 0.56},
            "4": {"name": "Proliferative Diabetic Retinopathy", "support": 58, "predicted_count": 50, "precision": 0.62, "recall": 0.53, "f1_score": 0.57},
        },
        "confusion_matrix": [[0] * 5 for _ in range(5)],
    }

    report_1 = generate_markdown_report(metrics_real_counts, output_path=tmp_path / "report_1.md")

    # Must contain actual validation counts (73, 39, 362)
    assert "73 samples" in report_1
    assert "39 samples" in report_1
    assert "362 samples" in report_1

    # Must NOT contain the old hardcoded inaccurate numbers (74 or 361)
    assert "74 samples" not in report_1
    assert "361 samples" not in report_1

    # Must contain development benchmark disclosure
    assert "development results, not independent clinical validation" in report_1 or \
           "internal development results on a held-out training partition, not independent clinical validation" in report_1

    # Test case 2: Arbitrary synthetic counts to guarantee full dynamism
    metrics_custom_counts = {
        "evaluated_at": "2026-10-17T12:00:00Z",
        "split_type": "validation",
        "is_independent_test_set": False,
        "total_samples": 695,
        "accuracy": 0.85,
        "macro_f1": 0.80,
        "weighted_f1": 0.84,
        "class_metrics": {
            "0": {"name": "No Diabetic Retinopathy", "support": 500, "precision": 0.9, "recall": 0.9, "f1_score": 0.9},
            "1": {"name": "Mild Non-Proliferative DR", "support": 150, "precision": 0.8, "recall": 0.8, "f1_score": 0.8},
            "2": {"name": "Moderate Non-Proliferative DR", "support": 0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0},
            "3": {"name": "Severe Non-Proliferative DR", "support": 45, "precision": 0.7, "recall": 0.7, "f1_score": 0.7},
            "4": {"name": "Proliferative Diabetic Retinopathy", "support": 0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0},
        },
    }

    report_2 = generate_markdown_report(metrics_custom_counts, output_path=tmp_path / "report_2.md")
    assert "150 samples" in report_2
    assert "45 samples" in report_2
    assert "500 samples" in report_2

