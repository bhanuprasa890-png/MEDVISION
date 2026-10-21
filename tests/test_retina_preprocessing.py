"""Automated test suite for MedVision AI RetinaGuard data preprocessing and dataset splitting."""

import csv
import io
import json
import tempfile
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest
from PIL import Image

from ai_models.retina.dataset import (
    DatasetValidationError,
    DatasetValidationReport,
    compute_class_weights,
    create_stratified_split,
    detect_csv_columns,
    find_project_root,
    generate_dataset_summary,
    load_aptos_csv,
    match_records_to_images,
    save_manifests,
    validate_dataset,
)
from ai_models.retina.preprocessing import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    RetinaImagePreprocessor,
    preprocess_retina_image,
)


@pytest.fixture
def project_root() -> Path:
    """Fixture providing repository root path."""
    return find_project_root()


@pytest.fixture
def aptos_dir(project_root: Path) -> Path:
    """Fixture providing APTOS dataset directory."""
    return project_root / "datasets" / "aptos"


# ==============================================================================
# PHASE 3: TESTS — CSV LOADING & COLUMN DETECTION
# ==============================================================================


def test_detect_csv_columns_standard():
    """Ensure standard APTOS headers ('id_code', 'diagnosis') are accurately resolved."""
    header = ["id_code", "diagnosis"]
    id_col, label_col = detect_csv_columns(header)
    assert id_col == "id_code"
    assert label_col == "diagnosis"


def test_detect_csv_columns_aliases():
    """Ensure column detector correctly maps aliases (e.g., 'image_id', 'label')."""
    header = ["Image_ID", "Label", "extra_notes"]
    id_col, label_col = detect_csv_columns(header)
    assert id_col == "Image_ID"
    assert label_col == "Label"


def test_detect_csv_columns_missing_raises_error():
    """Ensure missing ID or label columns trigger descriptive DatasetValidationError."""
    with pytest.raises(DatasetValidationError) as exc_info:
        detect_csv_columns(["patient_name", "date_of_scan"])
    assert "Failed to detect required columns" in str(exc_info.value)


def test_load_aptos_csv_real_dataset(aptos_dir: Path):
    """Verify loading of real APTOS train.csv and total row count (3,662 rows)."""
    csv_path = aptos_dir / "train.csv"
    assert csv_path.is_file(), f"APTOS train.csv not found at {csv_path}"

    records = load_aptos_csv(csv_path)
    assert len(records) == 3662
    # Verify first record fields
    first = records[0]
    assert "id_code" in first
    assert "diagnosis" in first
    assert first["id_code"] == "000c1434d8d7"
    assert int(first["diagnosis"]) == 2


# ==============================================================================
# PHASE 3: TESTS — IMAGE ID MATCHING & INTEGRITY VALIDATION
# ==============================================================================


def test_match_records_to_images(aptos_dir: Path, project_root: Path):
    """Verify image ID to PNG filename matching and relative path resolution."""
    sample_records = [
        {"id_code": "000c1434d8d7", "diagnosis": "2"},
        {"id_code": "001639a390f0", "diagnosis": "4"},
    ]
    img_dir = aptos_dir / "train_images"
    matched = match_records_to_images(sample_records, img_dir, project_root=project_root)

    assert len(matched) == 2
    assert matched[0]["image_path"] == "datasets/aptos/train_images/000c1434d8d7.png"
    assert matched[0]["file_exists"] is True
    assert matched[1]["image_path"] == "datasets/aptos/train_images/001639a390f0.png"
    assert matched[1]["file_exists"] is True


def test_validate_dataset_real_data(aptos_dir: Path):
    """Verify complete APTOS dataset passes validation with zero errors."""
    records = load_aptos_csv(aptos_dir / "train.csv")
    img_dir = aptos_dir / "train_images"

    report = validate_dataset(records, img_dir, strict=True)
    assert report.is_valid is True
    assert report.total_csv_rows == 3662
    assert len(report.missing_files) == 0
    assert len(report.duplicate_ids) == 0
    assert len(report.empty_images) == 0
    assert len(report.invalid_labels) == 0
    # Expected APTOS class distribution
    assert report.class_distribution == {0: 1805, 1: 370, 2: 999, 3: 193, 4: 295}


def test_validate_dataset_detects_missing_image(aptos_dir: Path):
    """Verify validator flags non-existent image files."""
    records = [{"id_code": "non_existent_image_id_9999", "diagnosis": "0"}]
    img_dir = aptos_dir / "train_images"

    report = validate_dataset(records, img_dir, strict=False)
    assert report.is_valid is False
    assert "non_existent_image_id_9999" in report.missing_files


def test_validate_dataset_detects_duplicate_ids(aptos_dir: Path):
    """Verify validator catches duplicate image IDs in CSV."""
    records = [
        {"id_code": "000c1434d8d7", "diagnosis": "2"},
        {"id_code": "000c1434d8d7", "diagnosis": "2"},
    ]
    img_dir = aptos_dir / "train_images"

    report = validate_dataset(records, img_dir, strict=False)
    assert report.is_valid is False
    assert "000c1434d8d7" in report.duplicate_ids


def test_validate_dataset_detects_invalid_labels(aptos_dir: Path):
    """Verify validator catches labels outside {0, 1, 2, 3, 4} or non-integer values."""
    records = [
        {"id_code": "000c1434d8d7", "diagnosis": "5"},   # Out of range (>4)
        {"id_code": "001639a390f0", "diagnosis": "-1"},  # Negative
        {"id_code": "0024cdab0c1e", "diagnosis": "bad"}, # Non-integer
    ]
    img_dir = aptos_dir / "train_images"

    report = validate_dataset(records, img_dir, strict=False)
    assert report.is_valid is False
    assert len(report.invalid_labels) == 3


def test_validate_dataset_detects_empty_image(tmp_path: Path):
    """Verify validator flags 0-byte image files."""
    # Create mock 0-byte file
    empty_file = tmp_path / "empty_img.png"
    empty_file.touch()

    records = [{"id_code": "empty_img", "diagnosis": "1"}]
    report = validate_dataset(records, tmp_path, check_file_sizes=True, strict=False)

    assert report.is_valid is False
    assert "empty_img" in report.empty_images


# ==============================================================================
# PHASE 3: TESTS — REPRODUCIBILITY & STRATIFIED SPLIT
# ==============================================================================


def test_stratified_split_reproducibility(aptos_dir: Path):
    """Verify that using the same random seed produces strictly identical splits."""
    records = load_aptos_csv(aptos_dir / "train.csv")

    train_1, val_1 = create_stratified_split(records, train_ratio=0.8, seed=42)
    train_2, val_2 = create_stratified_split(records, train_ratio=0.8, seed=42)

    train_ids_1 = [r["id_code"] for r in train_1]
    train_ids_2 = [r["id_code"] for r in train_2]
    val_ids_1 = [r["id_code"] for r in val_1]
    val_ids_2 = [r["id_code"] for r in val_2]

    assert train_ids_1 == train_ids_2
    assert val_ids_1 == val_ids_2


def test_stratified_split_different_seeds(aptos_dir: Path):
    """Verify that different random seeds produce different split partitions."""
    records = load_aptos_csv(aptos_dir / "train.csv")

    train_seed42, _ = create_stratified_split(records, train_ratio=0.8, seed=42)
    train_seed99, _ = create_stratified_split(records, train_ratio=0.8, seed=99)

    assert [r["id_code"] for r in train_seed42] != [r["id_code"] for r in train_seed99]


def test_stratified_split_no_overlap(aptos_dir: Path):
    """STRICT ASSERTION: Zero image ID overlap between training and validation splits."""
    records = load_aptos_csv(aptos_dir / "train.csv")
    train_records, val_records = create_stratified_split(records, train_ratio=0.8, seed=42)

    train_ids = {r["id_code"] for r in train_records}
    val_ids = {r["id_code"] for r in val_records}

    intersection = train_ids.intersection(val_ids)
    assert len(intersection) == 0, f"Data leakage detected! Overlapping IDs: {intersection}"
    assert len(train_records) + len(val_records) == 3662


def test_stratification_and_class_distribution(aptos_dir: Path):
    """Verify exact 80/20 stratification proportions across all 5 classes."""
    records = load_aptos_csv(aptos_dir / "train.csv")
    train_records, val_records = create_stratified_split(records, train_ratio=0.8, seed=42)

    expected_totals = {0: 1805, 1: 370, 2: 999, 3: 193, 4: 295}
    expected_train = {0: 1444, 1: 296, 2: 799, 3: 154, 4: 236}
    expected_val = {0: 361, 1: 74, 2: 200, 3: 39, 4: 59}

    train_counts: Dict[int, int] = {}
    for r in train_records:
        lbl = int(r["diagnosis"])
        train_counts[lbl] = train_counts.get(lbl, 0) + 1

    val_counts: Dict[int, int] = {}
    for r in val_records:
        lbl = int(r["diagnosis"])
        val_counts[lbl] = val_counts.get(lbl, 0) + 1

    assert train_counts == expected_train
    assert val_counts == expected_val

    # Verify per-class proportions match within 0.5% margin
    for c in range(5):
        ratio = train_counts[c] / expected_totals[c]
        assert abs(ratio - 0.8) <= 0.005, f"Class {c} split ratio deviated: {ratio}"


def test_class_weights_calculation(aptos_dir: Path):
    """Verify balanced class weights computation penalizes majority and upweights minority classes."""
    records = load_aptos_csv(aptos_dir / "train.csv")
    train_records, _ = create_stratified_split(records, train_ratio=0.8, seed=42)

    weights = compute_class_weights(train_records, num_classes=5, method="balanced")

    # Majority class (0) must have lowest weight
    # Minority class (3) must have highest weight
    assert weights[0] < weights[2] < weights[1] < weights[4] < weights[3]
    # Check expected balanced weights
    assert round(weights[0], 2) == 0.41
    assert round(weights[1], 2) == 1.98
    assert round(weights[2], 2) == 0.73
    assert round(weights[3], 2) == 3.80
    assert round(weights[4], 2) == 2.48


# ==============================================================================
# PHASE 3: TESTS — MANIFEST SAVING & VERIFICATION
# ==============================================================================


def test_manifest_files_and_relative_paths(aptos_dir: Path, project_root: Path):
    """Verify generated train_manifest.csv and val_manifest.csv on disk."""
    proc_dir = aptos_dir / "processed"
    train_manifest = proc_dir / "train_manifest.csv"
    val_manifest = proc_dir / "val_manifest.csv"
    summary_file = proc_dir / "dataset_summary.json"

    assert train_manifest.is_file(), "train_manifest.csv was not generated."
    assert val_manifest.is_file(), "val_manifest.csv was not generated."
    assert summary_file.is_file(), "dataset_summary.json was not generated."

    # Validate train manifest rows
    with open(train_manifest, mode="r", newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2929
        for row in reader[:10]:
            assert "id_code" in row
            assert "image_path" in row
            assert "diagnosis" in row
            assert "label" in row
            # Verify relative image path points to an actual file
            resolved_path = project_root / row["image_path"]
            assert resolved_path.is_file(), f"Path not found: {resolved_path}"

    # Validate val manifest rows
    with open(val_manifest, mode="r", newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 733
        for row in reader[:10]:
            resolved_path = project_root / row["image_path"]
            assert resolved_path.is_file(), f"Path not found: {resolved_path}"


# ==============================================================================
# PHASE 3: TESTS — IMAGE CONVERSION, RESIZING, AND NORMALIZATION
# ==============================================================================


def test_image_conversion_to_rgb():
    """Verify image converter converts L, RGBA, and palette modes to standard 3-channel RGB."""
    preprocessor = RetinaImagePreprocessor(target_size=(256, 256), normalize=False)

    # 1. Grayscale mode 'L'
    gray_img = Image.new("L", (100, 100), color=128)
    res_gray = preprocessor.convert_to_rgb(gray_img)
    assert res_gray.mode == "RGB"
    assert res_gray.size == (100, 100)

    # 2. RGBA mode
    rgba_img = Image.new("RGBA", (100, 100), color=(255, 100, 50, 200))
    res_rgba = preprocessor.convert_to_rgb(rgba_img)
    assert res_rgba.mode == "RGB"

    # 3. Already RGB
    rgb_img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    res_rgb = preprocessor.convert_to_rgb(rgb_img)
    assert res_rgb.mode == "RGB"


def test_image_resizing_configurable():
    """Verify image is accurately resized to configurable dimensions."""
    p_512 = RetinaImagePreprocessor(target_size=(512, 512), normalize=False)
    p_224 = RetinaImagePreprocessor(target_size=(224, 224), normalize=False)

    sample = Image.new("RGB", (1920, 1080), color=(50, 150, 250))

    img_512 = p_512.preprocess_pil(sample)
    assert img_512.size == (512, 512)

    img_224 = p_224.preprocess_pil(sample)
    assert img_224.size == (224, 224)


def test_image_normalization_imagenet_stats():
    """Verify ImageNet normalization produces zero-centered float32 array with (3, H, W) shape."""
    preprocessor = RetinaImagePreprocessor(
        target_size=(256, 256),
        normalize=True,
        channels_first=True,
        is_training=False,
    )

    sample = Image.new("RGB", (256, 256), color=(124, 116, 104))
    norm_tensor = preprocessor.preprocess(sample)

    assert isinstance(norm_tensor, np.ndarray)
    assert norm_tensor.shape == (3, 256, 256)
    assert norm_tensor.dtype == np.float32

    # Check channels-last option
    p_last = RetinaImagePreprocessor(
        target_size=(128, 128),
        normalize=True,
        channels_first=False,
        is_training=False,
    )
    last_tensor = p_last.preprocess(sample)
    assert last_tensor.shape == (128, 128, 3)


def test_denormalize_roundtrip():
    """Verify denormalization recovers valid [0, 255] uint8 RGB image."""
    preprocessor = RetinaImagePreprocessor(target_size=(128, 128), normalize=True, channels_first=True)
    orig_img = Image.new("RGB", (128, 128), color=(200, 100, 50))

    norm_arr = preprocessor.preprocess(orig_img)
    recovered = preprocessor.denormalize_array(norm_arr)

    assert recovered.shape == (128, 128, 3)
    assert recovered.dtype == np.uint8
    # Channel values should match within quantization tolerance (+- 2)
    assert abs(int(recovered[64, 64, 0]) - 200) <= 2
    assert abs(int(recovered[64, 64, 1]) - 100) <= 2
    assert abs(int(recovered[64, 64, 2]) - 50) <= 2


def test_validation_images_are_never_augmented():
    """CRITICAL RULE: Validation images must be deterministic and never randomly augmented."""
    preprocessor_eval = RetinaImagePreprocessor(
        target_size=(64, 64),
        is_training=False,  # Validation / Evaluation mode
        augment=True,        # Even if augment flag is set to True, it must be inactive
    )

    # Create an asymmetrical image
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:32, :32] = 255  # Top-left white square
    test_img = Image.fromarray(arr)

    # Run preprocessing 10 times
    first_output = preprocessor_eval.preprocess(test_img)
    for _ in range(10):
        subsequent_output = preprocessor_eval.preprocess(test_img)
        np.testing.assert_array_equal(first_output, subsequent_output)


def test_preprocess_retina_image_function(aptos_dir: Path):
    """Verify the backward-compatible preprocess_retina_image function."""
    sample_file = aptos_dir / "train_images" / "000c1434d8d7.png"
    with open(sample_file, "rb") as f:
        image_bytes = f.read()

    result = preprocess_retina_image(image_bytes, target_size=(512, 512), normalize=True)

    assert result["status"] == "SUCCESS"
    assert result["shape"] == [3, 512, 512]
    assert result["target_size"] == (512, 512)
    assert result["channels"] == 3
    assert isinstance(result["tensor"], np.ndarray)
    assert -3.0 <= result["min_value"] <= 3.0
    assert -3.0 <= result["max_value"] <= 3.0
