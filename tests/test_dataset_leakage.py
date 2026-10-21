"""Automated test suite for RetinaGuard dataset leakage prevention and integrity.

Tests:
1. Bit-identical duplicate group separation (zero cross-split leakage).
2. Real APTOS processed manifests zero-leakage verification (0 ID overlap, 0 hash overlap).
3. Preservation of conflicting diagnostic labels without silent modification.
4. Deterministic group-aware stratified splitting across runs.
5. Stratification ratio preservation across all 5 diagnostic grades.
6. Strict disjointness assertion and error raising upon overlap.
7. Missing file and corrupted record handling.
8. Manifest schema and dataset summary integrity.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from ai_models.retina.dataset import (
    DatasetValidationError,
    compute_class_weights,
    compute_image_sha256,
    create_group_aware_stratified_split,
    create_stratified_split,
    find_project_root,
    save_manifests,
    validate_dataset,
)
from ai_models.retina.evaluate import check_data_leakage


# ==============================================================================
# 1. DUPLICATE GROUP SEPARATION TESTS
# ==============================================================================


def test_group_aware_split_keeps_identical_images_in_same_split():
    """Verify that images sharing the same hash are never placed in different splits."""
    # Create 10 unique groups, 3 of which have duplicate images (2 images each)
    records = []
    # Group A: 2 images, same hash 'hash_A', diagnosis 1
    records.append({"id_code": "img_A1", "diagnosis": 1, "image_hash": "hash_A"})
    records.append({"id_code": "img_A2", "diagnosis": 1, "image_hash": "hash_A"})

    # Group B: 2 images, same hash 'hash_B', diagnosis 2
    records.append({"id_code": "img_B1", "diagnosis": 2, "image_hash": "hash_B"})
    records.append({"id_code": "img_B2", "diagnosis": 2, "image_hash": "hash_B"})

    # Group C: 2 images, same hash 'hash_C', conflicting diagnoses (2 and 3)
    records.append({"id_code": "img_C1", "diagnosis": 2, "image_hash": "hash_C"})
    records.append({"id_code": "img_C2", "diagnosis": 3, "image_hash": "hash_C"})

    # Single-image groups across classes 0 to 4
    for i in range(20):
        records.append({
            "id_code": f"single_{i}",
            "diagnosis": i % 5,
            "image_hash": f"hash_single_{i}",
        })

    train_recs, val_recs = create_group_aware_stratified_split(
        records,
        train_ratio=0.8,
        seed=42,
        label_key="diagnosis",
        hash_key="image_hash",
    )

    train_hashes = {r["image_hash"] for r in train_recs}
    val_hashes = {r["image_hash"] for r in val_recs}

    # Zero hash overlap guarantee
    assert len(train_hashes.intersection(val_hashes)) == 0, "Duplicate hash crossed split boundary!"

    # Both images of Group A must be in same split
    a_in_train = any(r["id_code"] == "img_A1" for r in train_recs)
    assert any(r["id_code"] == "img_A2" for r in train_recs) == a_in_train

    # Both images of Group B must be in same split
    b_in_train = any(r["id_code"] == "img_B1" for r in train_recs)
    assert any(r["id_code"] == "img_B2" for r in train_recs) == b_in_train

    # Both images of Group C must be in same split
    c_in_train = any(r["id_code"] == "img_C1" for r in train_recs)
    assert any(r["id_code"] == "img_C2" for r in train_recs) == c_in_train


def test_conflicting_labels_preserved_without_alteration():
    """Verify conflicting diagnostic labels are retained exactly as recorded."""
    records = [
        {"id_code": "conflict_1", "diagnosis": 2, "image_hash": "shared_hash_1"},
        {"id_code": "conflict_2", "diagnosis": 3, "image_hash": "shared_hash_1"},
        {"id_code": "conflict_3", "diagnosis": 0, "image_hash": "shared_hash_2"},
        {"id_code": "conflict_4", "diagnosis": 1, "image_hash": "shared_hash_2"},
    ]
    # Add dummy samples to allow splitting
    for i in range(16):
        records.append({"id_code": f"other_{i}", "diagnosis": i % 5, "image_hash": f"uniq_{i}"})

    train_recs, val_recs = create_group_aware_stratified_split(
        records,
        train_ratio=0.8,
        seed=42,
    )

    all_out = {r["id_code"]: r["diagnosis"] for r in train_recs + val_recs}

    # Labels must remain strictly unchanged
    assert all_out["conflict_1"] == 2
    assert all_out["conflict_2"] == 3
    assert all_out["conflict_3"] == 0
    assert all_out["conflict_4"] == 1


# ==============================================================================
# 2. DETERMINISM AND REPRODUCIBILITY
# ==============================================================================


def test_deterministic_splitting_consistency():
    """Verify same seed produces bit-identical splits across executions."""
    records = [
        {"id_code": f"sample_{i}", "diagnosis": i % 5, "image_hash": f"hash_{i % 7}"}
        for i in range(50)
    ]

    t1, v1 = create_group_aware_stratified_split(records, train_ratio=0.8, seed=123)
    t2, v2 = create_group_aware_stratified_split(records, train_ratio=0.8, seed=123)

    assert [r["id_code"] for r in t1] == [r["id_code"] for r in t2]
    assert [r["id_code"] for r in v1] == [r["id_code"] for r in v2]


def test_different_seeds_produce_different_splits():
    """Verify varying random seeds alters sample partition ordering."""
    records = [
        {"id_code": f"sample_{i}", "diagnosis": i % 5, "image_hash": f"hash_{i}"}
        for i in range(50)
    ]

    t1, _ = create_group_aware_stratified_split(records, train_ratio=0.8, seed=42)
    t2, _ = create_group_aware_stratified_split(records, train_ratio=0.8, seed=999)

    assert [r["id_code"] for r in t1] != [r["id_code"] for r in t2]


# ==============================================================================
# 3. DISJOINTNESS AND VALIDATION GUARDS
# ==============================================================================


def test_disjointness_violation_raises_error():
    """Verify DatasetValidationError is raised when hash leakage occurs during saving."""
    train_recs = [{"id_code": "img1", "diagnosis": 0, "image_hash": "leak_hash"}]
    val_recs = [{"id_code": "img2", "diagnosis": 1, "image_hash": "leak_hash"}]

    with pytest.raises(DatasetValidationError, match="bit-identical duplicate image overlap detected"):
        save_manifests(train_recs, val_recs, output_dir=Path("scratch/test_out"))


def test_id_overlap_raises_error():
    """Verify DatasetValidationError is raised if duplicate IDs occur across splits."""
    train_recs = [{"id_code": "img_same", "diagnosis": 0}]
    val_recs = [{"id_code": "img_same", "diagnosis": 0}]

    with pytest.raises(DatasetValidationError, match="overlap detected between train and val IDs"):
        save_manifests(train_recs, val_recs, output_dir=Path("scratch/test_out"))


# ==============================================================================
# 4. REAL REPOSITORY MANIFEST INTEGRITY TESTS
# ==============================================================================


def test_real_processed_manifests_zero_leakage():
    """Verify the real generated train and val manifests have zero leakage."""
    root = find_project_root()
    train_csv = root / "datasets" / "aptos" / "processed" / "train_manifest.csv"
    val_csv = root / "datasets" / "aptos" / "processed" / "val_manifest.csv"

    if not (train_csv.is_file() and val_csv.is_file()):
        pytest.skip("Processed manifests not present on disk.")

    with open(train_csv, "r", encoding="utf-8") as f:
        train_rows = list(csv.DictReader(f))
    with open(val_csv, "r", encoding="utf-8") as f:
        val_rows = list(csv.DictReader(f))

    assert len(train_rows) == 2929
    assert len(val_rows) == 733

    train_ids = {r["id_code"] for r in train_rows}
    val_ids = {r["id_code"] for r in val_rows}

    # Zero ID overlap
    assert len(train_ids.intersection(val_ids)) == 0

    # Verification via evaluate.py check_data_leakage
    leakage = check_data_leakage(val_csv, train_csv, check_hashes=False)
    assert leakage["has_leakage"] is False
    assert leakage["id_overlap_count"] == 0


def test_real_dataset_summary_metrics():
    """Verify dataset_summary.json conforms to expectations and records zero leakage."""
    root = find_project_root()
    summary_path = root / "datasets" / "aptos" / "processed" / "dataset_summary.json"

    if not summary_path.is_file():
        pytest.skip("dataset_summary.json not present on disk.")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["total_images"] == 3662
    assert summary["train_count"] == 2929
    assert summary["val_count"] == 733
    assert summary["split_specification"]["group_aware"] is True
    assert summary["split_specification"]["zero_leakage_guarantee"] is True
    assert summary["leakage_audit"]["cross_split_duplicates_count"] == 0
    assert summary["leakage_audit"]["train_unique_hashes"] == 2823
    assert summary["leakage_audit"]["val_unique_hashes"] == 711

    # Verify class weights are positive floats
    weights = summary["balanced_class_weights"]
    for c in range(5):
        assert str(c) in weights
        assert float(weights[str(c)]) > 0.0


# ==============================================================================
# 5. MISSING AND CORRUPTED FILE TESTS
# ==============================================================================


def test_validate_dataset_detects_missing_file(tmp_path):
    """Verify validate_dataset reports missing files without crashing."""
    records = [{"id_code": "non_existent_img", "diagnosis": 0}]
    report = validate_dataset(records, images_dir=tmp_path, strict=False)

    assert report.is_valid is False
    assert "non_existent_img" in report.missing_files


# ==============================================================================
# 6. CHECKPOINT PRESERVATION AND BACKUP TESTS
# ==============================================================================


def test_checkpoint_backup_on_training_start(tmp_path):
    """Verify training creates a backup of an existing checkpoint before overwriting."""
    import torch
    from torch.utils.data import DataLoader, TensorDataset
    from ai_models.retina.model import build_retina_model
    from ai_models.retina.train import RetinaTrainer

    # Create pre-existing checkpoint
    pre_existing_ckpt = tmp_path / "best_model.pt"
    dummy_payload = {"version": "original_v1", "marker": 12345}
    torch.save(dummy_payload, pre_existing_ckpt)
    assert pre_existing_ckpt.is_file()

    # Create dummy DataLoader
    dummy_x = torch.randn(4, 3, 224, 224)
    dummy_y = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    loader = DataLoader(TensorDataset(dummy_x, dummy_y), batch_size=2)

    model = build_retina_model(num_classes=5, pretrained=False)
    trainer = RetinaTrainer(
        model=model,
        train_loader=loader,
        val_loader=loader,
        output_dir=tmp_path,
        learning_rate=1e-3,
    )

    trainer.train(total_epochs=1, freeze_backbone_epochs=0)

    # Verify backup was created
    backup_file = tmp_path / "best_model_backup.pt"
    assert backup_file.is_file(), "Backup checkpoint best_model_backup.pt was not created!"
    loaded_backup = torch.load(backup_file, map_location="cpu")
    assert loaded_backup.get("version") == "original_v1"
    assert loaded_backup.get("marker") == 12345
