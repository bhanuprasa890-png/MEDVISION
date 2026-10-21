"""Dataset loading, validation, stratified splitting, and manifest pipeline for RetinaGuard.

Handles the APTOS 2019 Blindness Detection dataset and related retinal classification datasets:
1. Project-root agnostic path resolution (portable across development environments).
2. CSV parsing and intelligent header detection (supports 'id_code' / 'diagnosis' and standard aliases).
3. Comprehensive dataset integrity validation:
   - Missing image files
   - Duplicate image IDs
   - Empty / 0-byte images
   - Labels outside permitted class space (0, 1, 2, 3, 4)
   - Orphan image files on disk
4. Reproducible, stratified 80% train / 20% validation split with deterministic random seed.
5. Strict disjointness guarantee (zero ID overlap between train and validation splits).
6. Manifest export under datasets/aptos/processed/ (train_manifest.csv, val_manifest.csv).
7. Training-time class imbalance mitigation (balanced class weights computation).
8. Comprehensive summary metrics export (dataset_summary.json).
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import os
import random
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

logger = logging.getLogger("medvision.retina.dataset")


class DatasetValidationError(Exception):
    """Raised when dataset integrity or format validation fails."""

    def __init__(self, message: str, report: Optional["DatasetValidationReport"] = None) -> None:
        super().__init__(message)
        self.report = report


@dataclass
class DatasetValidationReport:
    """Detailed summary of dataset integrity checks."""

    total_csv_rows: int = 0
    valid_records: int = 0
    missing_files: List[str] = field(default_factory=list)
    duplicate_ids: List[str] = field(default_factory=list)
    empty_images: List[str] = field(default_factory=list)
    corrupted_images: List[str] = field(default_factory=list)
    invalid_labels: List[Tuple[str, Any]] = field(default_factory=list)
    orphan_files: List[str] = field(default_factory=list)
    class_distribution: Dict[int, int] = field(default_factory=dict)
    is_valid: bool = True
    error_messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to serializable dictionary."""
        return asdict(self)


def find_project_root(anchor: Union[Path, str, None] = None) -> Path:
    """Find the root directory of the MedVision AI project.

    Searches upward from the anchor location (or current directory / module file)
    until key marker directories ('datasets', 'backend', '.git') are discovered.

    Args:
        anchor: Optional starting path or file.

    Returns:
        Absolute Path object for the detected project root.
    """
    if "MEDVISION_ROOT" in os.environ:
        return Path(os.environ["MEDVISION_ROOT"]).resolve()

    start = Path(anchor or Path.cwd()).resolve()
    if start.is_file():
        start = start.parent

    for candidate in [start, *start.parents]:
        if (candidate / "datasets" / "aptos").is_dir() or (candidate / "backend").is_dir():
            return candidate

    # Fallback: relative to this file (ai_models/retina/dataset.py -> root is 3 levels up)
    return Path(__file__).resolve().parents[2]


def detect_csv_columns(
    header: Sequence[str],
    id_candidates: Sequence[str] = ("id_code", "image_id", "id", "filename", "image_name"),
    label_candidates: Sequence[str] = ("diagnosis", "label", "target", "class", "dr_level"),
) -> Tuple[str, str]:
    """Detect image ID and label column names from CSV header.

    Args:
        header: List or tuple of header column strings.
        id_candidates: Preferred candidate names for the ID column.
        label_candidates: Preferred candidate names for the label column.

    Returns:
        Tuple of (id_column_name, label_column_name).

    Raises:
        DatasetValidationError: If either column cannot be identified.
    """
    clean_header = [col.strip() for col in header]
    clean_lower = {col.lower(): col for col in clean_header}

    id_col = None
    for cand in id_candidates:
        if cand.lower() in clean_lower:
            id_col = clean_lower[cand.lower()]
            break

    label_col = None
    for cand in label_candidates:
        if cand.lower() in clean_lower:
            label_col = clean_lower[cand.lower()]
            break

    if not id_col or not label_col:
        raise DatasetValidationError(
            f"Failed to detect required columns in CSV header: {header}. "
            f"Found ID='{id_col}', Label='{label_col}'. "
            f"Expected candidates: ID in {list(id_candidates)}, Label in {list(label_candidates)}."
        )

    return id_col, label_col


def load_aptos_csv(
    csv_path: Union[Path, str],
    id_col: Optional[str] = None,
    label_col: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load and parse the APTOS train.csv annotations file.

    Args:
        csv_path: Path to the CSV file.
        id_col: Explicit name of the image ID column (auto-detected if None).
        label_col: Explicit name of the label column (auto-detected if None).

    Returns:
        List of dictionaries with keys: 'id_code', 'diagnosis', 'row_index'.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        DatasetValidationError: If CSV is empty or malformed.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Annotation CSV file not found: {path}")

    records: List[Dict[str, Any]] = []

    with open(path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise DatasetValidationError(f"CSV file is empty: {path}")

        # Detect or validate columns
        detected_id_col, detected_label_col = detect_csv_columns(header)
        actual_id_col = id_col or detected_id_col
        actual_label_col = label_col or detected_label_col

        clean_header = [h.strip() for h in header]
        try:
            id_idx = clean_header.index(actual_id_col)
            label_idx = clean_header.index(actual_label_col)
        except ValueError as err:
            raise DatasetValidationError(
                f"Specified column not found in header {clean_header}: {err}"
            ) from err

        for row_idx, row in enumerate(reader, start=2):  # Line 1 is header
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip trailing blank lines
            if len(row) <= max(id_idx, label_idx):
                continue

            raw_id = row[id_idx].strip()
            raw_label = row[label_idx].strip()

            records.append(
                {
                    "id_code": raw_id,
                    "diagnosis": raw_label,
                    "row_index": row_idx,
                }
            )

    return records


def match_records_to_images(
    records: List[Dict[str, Any]],
    images_dir: Union[Path, str],
    project_root: Optional[Union[Path, str]] = None,
    extension: str = ".png",
) -> List[Dict[str, Any]]:
    """Match each image record to its corresponding file on disk and compute relative path.

    Args:
        records: List of record dictionaries containing 'id_code'.
        images_dir: Directory containing retinal images.
        project_root: Root directory for computing portable relative paths.
        extension: Expected file extension (defaults to '.png').

    Returns:
        List of updated record dicts with 'image_path' (relative) and 'absolute_path'.
    """
    img_dir_path = Path(images_dir).resolve()
    root_path = Path(project_root or find_project_root()).resolve()

    matched: List[Dict[str, Any]] = []

    for rec in records:
        img_id = rec["id_code"]
        # Handle cases where id_code already includes extension
        filename = img_id if img_id.lower().endswith(extension.lower()) else f"{img_id}{extension}"
        abs_file = img_dir_path / filename

        # Compute portable relative path relative to project root
        try:
            rel_file = abs_file.relative_to(root_path)
            rel_path_str = str(rel_file).replace("\\", "/")
        except ValueError:
            rel_path_str = str(abs_file).replace("\\", "/")

        rec_copy = dict(rec)
        rec_copy["image_path"] = rel_path_str
        rec_copy["absolute_path"] = str(abs_file)
        rec_copy["file_exists"] = abs_file.is_file()
        matched.append(rec_copy)

    return matched


def validate_dataset(
    records: List[Dict[str, Any]],
    images_dir: Union[Path, str],
    valid_labels: Set[int] = frozenset({0, 1, 2, 3, 4}),  # type: ignore[assignment]
    check_file_sizes: bool = True,
    strict: bool = False,
) -> DatasetValidationReport:
    """Validate dataset integrity according to medical AI quality criteria.

    Validates:
    1. Duplicate image IDs.
    2. Missing physical image files.
    3. Empty (0-byte) image files.
    4. Labels outside valid domain {0, 1, 2, 3, 4} or non-integer values.
    5. Orphan image files present in directory but absent from CSV.

    Args:
        records: List of parsed records containing 'id_code' and 'diagnosis'.
        images_dir: Path to directory housing image files.
        valid_labels: Permitted class label integer values.
        check_file_sizes: Whether to verify files are not empty (0 bytes).
        strict: If True, raises DatasetValidationError upon encountering any failure.

    Returns:
        DatasetValidationReport with complete verification breakdown.

    Raises:
        DatasetValidationError: If strict=True and any integrity violations exist.
    """
    img_dir = Path(images_dir).resolve()
    report = DatasetValidationReport(total_csv_rows=len(records))

    seen_ids: Set[str] = set()
    class_counts: Dict[int, int] = {}

    for rec in records:
        img_id = rec.get("id_code", "").strip()
        raw_label = rec.get("diagnosis")

        # 1. Duplicate ID validation
        if not img_id:
            report.error_messages.append("Encountered record with empty ID code.")
            report.is_valid = False
            continue

        if img_id in seen_ids:
            report.duplicate_ids.append(img_id)
            report.is_valid = False
        seen_ids.add(img_id)

        # 2. Label validation
        parsed_label: Optional[int] = None
        try:
            parsed_label = int(raw_label)  # type: ignore[arg-type]
            if parsed_label not in valid_labels:
                report.invalid_labels.append((img_id, parsed_label))
                report.is_valid = False
            else:
                class_counts[parsed_label] = class_counts.get(parsed_label, 0) + 1
        except (ValueError, TypeError):
            report.invalid_labels.append((img_id, raw_label))
            report.is_valid = False

        # 3. File existence and non-empty check
        filename = f"{img_id}.png" if not img_id.endswith(".png") else img_id
        file_path = img_dir / filename

        if not file_path.is_file():
            report.missing_files.append(img_id)
            report.is_valid = False
        elif check_file_sizes:
            try:
                if file_path.stat().st_size == 0:
                    report.empty_images.append(img_id)
                    report.is_valid = False
            except OSError as err:
                report.error_messages.append(f"Could not stat image file {file_path}: {err}")
                report.is_valid = False

    # 4. Check for orphan images on disk (files in dir not present in CSV)
    if img_dir.is_dir():
        disk_files = {
            f.stem for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() == ".png"
        }
        orphans = disk_files - seen_ids
        report.orphan_files = sorted(orphans)

    report.valid_records = len(seen_ids) - len(report.missing_files) - len(report.empty_images) - len(report.invalid_labels)
    report.class_distribution = dict(sorted(class_counts.items()))

    if report.duplicate_ids:
        report.error_messages.append(f"Found {len(report.duplicate_ids)} duplicate image IDs.")
    if report.missing_files:
        report.error_messages.append(f"Found {len(report.missing_files)} missing image files.")
    if report.empty_images:
        report.error_messages.append(f"Found {len(report.empty_images)} empty (0-byte) images.")
    if report.invalid_labels:
        report.error_messages.append(f"Found {len(report.invalid_labels)} invalid labels outside {valid_labels}.")

    if strict and not report.is_valid:
        raise DatasetValidationError(
            f"Dataset validation failed: {'; '.join(report.error_messages)}",
            report=report,
        )

    return report


def create_stratified_split(
    records: List[Dict[str, Any]],
    train_ratio: float = 0.8,
    seed: int = 42,
    label_key: str = "diagnosis",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Partition records into reproducible, stratified training and validation splits.

    Guarantees:
    1. Stratification: Each class distribution in train and val strictly mirrors the full dataset.
    2. Reproducibility: Identical seed produces identical splits across platforms and executions.
    3. Disjointness: Zero image ID overlap between training and validation splits.

    Args:
        records: List of record dictionaries.
        train_ratio: Proportion of each class allocated to training (default 0.8 for 80/20 split).
        seed: Random seed for deterministic shuffling.
        label_key: Dictionary key containing the integer class label.

    Returns:
        Tuple of (train_records, val_records).

    Raises:
        ValueError: If train_ratio is outside (0.0, 1.0) or records list is empty.
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError(f"train_ratio must be strictly between 0.0 and 1.0, got {train_ratio}")
    if not records:
        raise ValueError("Cannot split an empty records list.")

    # Group records by class label
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for rec in records:
        lbl = int(rec[label_key])
        grouped.setdefault(lbl, []).append(rec)

    train_records: List[Dict[str, Any]] = []
    val_records: List[Dict[str, Any]] = []

    # Sort class keys to guarantee deterministic ordering across runs
    for class_label in sorted(grouped.keys()):
        class_items = grouped[class_label]
        # Sort items deterministically by id_code before shuffling
        class_items_sorted = sorted(class_items, key=lambda x: str(x.get("id_code", "")))

        # Use deterministic RNG per class based on seed and class label
        rng = random.Random(seed + class_label)
        shuffled = list(class_items_sorted)
        rng.shuffle(shuffled)

        # Compute exact split boundary (rounded to nearest integer)
        n_train = int(round(len(shuffled) * train_ratio))
        # Ensure at least 1 sample in validation if class has >= 2 items
        if n_train == len(shuffled) and len(shuffled) > 1:
            n_train = len(shuffled) - 1

        train_part = shuffled[:n_train]
        val_part = shuffled[n_train:]

        train_records.extend(train_part)
        val_records.extend(val_part)

    # STRICT INTEGRITY CHECK: Disjointness assertion
    train_ids = {r["id_code"] for r in train_records}
    val_ids = {r["id_code"] for r in val_records}
    overlap = train_ids.intersection(val_ids)
    if overlap:
        raise DatasetValidationError(
            f"Data leakage detected! {len(overlap)} IDs present in both splits: {list(overlap)[:5]}"
        )

    return train_records, val_records


def compute_image_sha256(filepath: Union[Path, str]) -> str:
    """Compute deterministic SHA-256 hex digest for an image file.

    Args:
        filepath: Path to the image file on disk.

    Returns:
        Hexadecimal SHA-256 digest string.

    Raises:
        FileNotFoundError: If the image file does not exist.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found for hashing: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_group_aware_stratified_split(
    records: List[Dict[str, Any]],
    images_dir: Optional[Union[Path, str]] = None,
    train_ratio: float = 0.8,
    seed: int = 42,
    label_key: str = "diagnosis",
    hash_key: str = "image_hash",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Partition records into reproducible, leakage-free, group-aware stratified splits.

    Guarantees:
    1. Zero Data Leakage: All bit-identical images (sharing the exact same SHA-256 hash)
       are placed atomically into either the training split or validation split. No group crosses
       the train/validation split boundary.
    2. Preservation of Diagnostic Annotations: The underlying clinical diagnosis label of each
       individual image record is preserved exactly as recorded; labels are never modified or overwritten.
    3. Stratification: Groups are stratified by their primary consensus class label to maintain
       proportional representation of each DR grade (classes 0-4) across splits.
    4. Deterministic Reproducibility: Given the same seed, identical splits are produced across all platforms.
    5. Strict Disjointness: Asserts zero image ID overlap and zero image hash overlap between splits.

    Args:
        records: List of record dictionaries.
        images_dir: Optional directory containing retinal images for computing hashes if absent.
        train_ratio: Proportion of samples allocated to training (default 0.8 for 80/20 split).
        seed: Random seed for deterministic shuffling.
        label_key: Dictionary key containing the integer class label.
        hash_key: Dictionary key containing the SHA-256 hash string.

    Returns:
        Tuple of (train_records, val_records).

    Raises:
        ValueError: If train_ratio is outside (0.0, 1.0) or records list is empty.
        DatasetValidationError: If any split-crossing data leakage or ID overlap occurs.
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError(f"train_ratio must be strictly between 0.0 and 1.0, got {train_ratio}")
    if not records:
        raise ValueError("Cannot split an empty records list.")

    root = find_project_root()
    img_dir_path = Path(images_dir).resolve() if images_dir else None

    # Step 1: Ensure hash is available on all records
    hash_to_records: Dict[str, List[Dict[str, Any]]] = {}

    for rec in records:
        h = rec.get(hash_key)
        if not h:
            candidate_paths: List[Path] = []
            if "absolute_path" in rec and rec["absolute_path"]:
                candidate_paths.append(Path(rec["absolute_path"]))
            if img_dir_path:
                candidate_paths.append(img_dir_path / f"{rec['id_code']}.png")
                candidate_paths.append(img_dir_path / rec["id_code"])
            if "image_path" in rec and rec["image_path"]:
                candidate_paths.append(root / rec["image_path"])

            computed_hash = None
            for p in candidate_paths:
                if p.is_file():
                    computed_hash = compute_image_sha256(p)
                    break

            # Fallback for synthetic/unit-test records without files on disk
            h = computed_hash or str(rec.get("id_code", ""))
            rec[hash_key] = h

        hash_to_records.setdefault(h, []).append(rec)

    # Step 2: Assign primary consensus class per group for stratification
    groups: List[Dict[str, Any]] = []
    for h, recs in hash_to_records.items():
        labels = [int(r[label_key]) for r in recs]
        counts = Counter(labels)
        # Primary class: highest frequency, breaking ties deterministically by lowest class integer
        primary_class = sorted(counts.keys(), key=lambda c: (-counts[c], c))[0]
        groups.append({
            "hash": h,
            "records": recs,
            "primary_class": primary_class,
            "size": len(recs),
            "labels": labels,
        })

    # Step 3: Group groups by primary class
    groups_by_class: Dict[int, List[Dict[str, Any]]] = {}
    for g in groups:
        groups_by_class.setdefault(g["primary_class"], []).append(g)

    train_records: List[Dict[str, Any]] = []
    val_records: List[Dict[str, Any]] = []

    # Step 4: Deterministic stratified allocation per class
    for class_label in sorted(groups_by_class.keys()):
        c_groups = sorted(groups_by_class[class_label], key=lambda x: str(x["hash"]))
        rng = random.Random(seed + class_label)
        rng.shuffle(c_groups)

        total_samples = sum(g["size"] for g in c_groups)
        target_train = int(round(total_samples * train_ratio))

        curr_train = 0
        c_train: List[Dict[str, Any]] = []
        c_val: List[Dict[str, Any]] = []

        for g in c_groups:
            if curr_train + g["size"] <= target_train:
                c_train.append(g)
                curr_train += g["size"]
            else:
                c_val.append(g)

        # Ensure non-empty splits if a class has at least 2 groups
        if len(c_val) == 0 and len(c_groups) > 1:
            c_val.append(c_train.pop())
        if len(c_train) == 0 and len(c_groups) > 1:
            c_train.append(c_val.pop())

        for g in c_train:
            train_records.extend(g["records"])
        for g in c_val:
            val_records.extend(g["records"])

    # Step 5: Assert zero leakage and strict disjointness
    train_hashes = {r[hash_key] for r in train_records}
    val_hashes = {r[hash_key] for r in val_records}
    hash_overlap = train_hashes.intersection(val_hashes)
    if hash_overlap:
        raise DatasetValidationError(
            f"Bit-identical image leakage detected! {len(hash_overlap)} image hash groups crossed the split boundary."
        )

    train_ids = {r["id_code"] for r in train_records}
    val_ids = {r["id_code"] for r in val_records}
    id_overlap = train_ids.intersection(val_ids)
    if id_overlap:
        raise DatasetValidationError(
            f"ID overlap detected! {len(id_overlap)} IDs present in both splits: {list(id_overlap)[:5]}"
        )

    return train_records, val_records


def compute_class_weights(
    records_or_labels: Union[List[Dict[str, Any]], List[int], Sequence[int]],
    num_classes: int = 5,
    method: str = "balanced",
    label_key: str = "diagnosis",
) -> Dict[int, float]:
    """Calculate balanced loss weights to handle diabetic retinopathy class imbalance.

    Heuristic follows the standard balanced formulation:
        w_c = N / (K * N_c)
    where N is total training samples, K is number of classes, and N_c is frequency of class c.

    CRITICAL: Applied exclusively to training loss. Validation examples are never duplicated.

    Args:
        records_or_labels: List of record dicts or list of integer labels.
        num_classes: Total number of classes (default 5 for APTOS 0-4).
        method: Weight calculation strategy ('balanced' or 'inverse').
        label_key: Dict key to extract label when passing record dicts.

    Returns:
        Dictionary mapping class integer to float weight.
    """
    labels: List[int] = []
    if records_or_labels and isinstance(records_or_labels[0], dict):
        labels = [int(r[label_key]) for r in records_or_labels]  # type: ignore[index]
    else:
        labels = [int(lbl) for lbl in records_or_labels]  # type: ignore[union-attr]

    total_samples = len(labels)
    if total_samples == 0:
        return {c: 1.0 for c in range(num_classes)}

    counts: Dict[int, int] = {}
    for lbl in labels:
        counts[lbl] = counts.get(lbl, 0) + 1

    weights: Dict[int, float] = {}

    for c in range(num_classes):
        cnt = counts.get(c, 0)
        if cnt == 0:
            weights[c] = 1.0
            continue

        if method == "balanced":
            # w = total / (num_classes * count)
            w = total_samples / (num_classes * cnt)
        elif method == "inverse":
            w = 1.0 / cnt
        else:
            raise ValueError(f"Unknown class weight calculation method: {method}")

        weights[c] = round(float(w), 6)

    return weights


def save_manifests(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    output_dir: Union[Path, str],
    project_root: Optional[Union[Path, str]] = None,
) -> Tuple[Path, Path]:
    """Save training and validation split manifests to disk.

    Output files:
    - {output_dir}/train_manifest.csv
    - {output_dir}/val_manifest.csv

    Columns:
    - id_code: Unique image identifier
    - image_path: Portable relative image path
    - diagnosis: Integer diabetic retinopathy grade (0-4)
    - label: Standardized label alias (0-4)

    Args:
        train_records: List of training records.
        val_records: List of validation records.
        output_dir: Destination directory (e.g. datasets/aptos/processed).
        project_root: Root directory for relative path verification.

    Returns:
        Tuple of (train_manifest_path, val_manifest_path).
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    train_path = out_dir / "train_manifest.csv"
    val_path = out_dir / "val_manifest.csv"

    # Verify disjointness prior to write
    train_ids = {r["id_code"] for r in train_records}
    val_ids = {r["id_code"] for r in val_records}
    if train_ids.intersection(val_ids):
        raise DatasetValidationError("Cannot save manifests: overlap detected between train and val IDs.")

    # Verify image hash disjointness if hashes exist
    train_hashes = {r["image_hash"] for r in train_records if "image_hash" in r}
    val_hashes = {r["image_hash"] for r in val_records if "image_hash" in r}
    if train_hashes and val_hashes and train_hashes.intersection(val_hashes):
        raise DatasetValidationError("Cannot save manifests: bit-identical duplicate image overlap detected between train and val splits.")

    fieldnames = ["id_code", "image_path", "diagnosis", "label"]

    def _write_csv(records: List[Dict[str, Any]], filepath: Path) -> None:
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                diag = int(r["diagnosis"])
                writer.writerow(
                    {
                        "id_code": r["id_code"],
                        "image_path": r.get("image_path", f"datasets/aptos/train_images/{r['id_code']}.png"),
                        "diagnosis": diag,
                        "label": diag,
                    }
                )

    _write_csv(train_records, train_path)
    _write_csv(val_records, val_path)

    return train_path, val_path


def generate_dataset_summary(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    class_weights: Dict[int, float],
    output_json_path: Optional[Union[Path, str]] = None,
    is_group_aware: bool = True,
) -> Dict[str, Any]:
    """Generate and optionally persist comprehensive distribution metadata.

    Args:
        train_records: Training split records.
        val_records: Validation split records.
        class_weights: Calculated class weights.
        output_json_path: Optional destination path for saving summary JSON.
        is_group_aware: Whether group-aware atomic clustering was enforced to eliminate duplicate leakage.

    Returns:
        Dictionary containing structured dataset metrics.
    """
    class_names = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative DR",
    }

    train_counts: Dict[int, int] = {}
    for r in train_records:
        lbl = int(r["diagnosis"])
        train_counts[lbl] = train_counts.get(lbl, 0) + 1

    val_counts: Dict[int, int] = {}
    for r in val_records:
        lbl = int(r["diagnosis"])
        val_counts[lbl] = val_counts.get(lbl, 0) + 1

    total_train = len(train_records)
    total_val = len(val_records)
    total_all = total_train + total_val

    classes_summary = {}
    for c in range(5):
        t_cnt = train_counts.get(c, 0)
        v_cnt = val_counts.get(c, 0)
        c_tot = t_cnt + v_cnt
        classes_summary[str(c)] = {
            "name": class_names.get(c, f"Class {c}"),
            "total_count": c_tot,
            "total_percent": round((c_tot / total_all) * 100, 2) if total_all else 0,
            "train_count": t_cnt,
            "train_percent": round((t_cnt / total_train) * 100, 2) if total_train else 0,
            "val_count": v_cnt,
            "val_percent": round((v_cnt / total_val) * 100, 2) if total_val else 0,
            "train_split_ratio": round(t_cnt / c_tot, 4) if c_tot else 0,
            "class_weight": class_weights.get(c, 1.0),
        }

    train_hashes = {r["image_hash"] for r in train_records if "image_hash" in r}
    val_hashes = {r["image_hash"] for r in val_records if "image_hash" in r}
    hash_overlap_count = len(train_hashes.intersection(val_hashes)) if (train_hashes and val_hashes) else 0

    summary: Dict[str, Any] = {
        "dataset_name": "APTOS 2019 Blindness Detection",
        "modality": "retinal_fundus",
        "total_images": total_all,
        "split_specification": {
            "train_ratio": 0.80,
            "val_ratio": 0.20,
            "random_seed": 42,
            "stratified": True,
            "group_aware": is_group_aware,
            "zero_leakage_guarantee": is_group_aware,
        },
        "leakage_audit": {
            "group_aware": is_group_aware,
            "cross_split_duplicates_count": hash_overlap_count,
            "train_unique_hashes": len(train_hashes) if train_hashes else None,
            "val_unique_hashes": len(val_hashes) if val_hashes else None,
        },
        "train_count": total_train,
        "val_count": total_val,
        "classes": classes_summary,
        "balanced_class_weights": {str(k): v for k, v in class_weights.items()},
    }

    if output_json_path:
        out_p = Path(output_json_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    return summary


def run_retina_data_pipeline(
    data_dir: Optional[Union[Path, str]] = None,
    output_dir: Optional[Union[Path, str]] = None,
    seed: int = 42,
    train_ratio: float = 0.8,
    group_aware: bool = True,
) -> Dict[str, Any]:
    """Execute end-to-end data preparation and manifest generation for RetinaGuard.

    Workflow:
    1. Locates project root and dataset directory.
    2. Reads and parses annotations CSV.
    3. Matches IDs to PNG images on disk.
    4. Runs exhaustive validation checks.
    5. Performs group-aware stratified 80/20 split with fixed seed (zero image leakage).
    6. Verifies complete ID and image hash disjointness.
    7. Computes balanced class weights.
    8. Exports manifests and summary metrics.

    Args:
        data_dir: Directory containing train.csv and train_images/ (default: datasets/aptos).
        output_dir: Directory for processed manifests (default: datasets/aptos/processed).
        seed: Random seed for reproducibility.
        train_ratio: Fraction for training split (default: 0.8).
        group_aware: If True, clusters duplicate images atomically by SHA-256 to guarantee 0 leakage.

    Returns:
        Dictionary reporting pipeline status, manifest paths, and split metrics.
    """
    root = find_project_root()
    base_data = Path(data_dir).resolve() if data_dir else (root / "datasets" / "aptos")
    csv_file = base_data / "train.csv"
    img_dir = base_data / "train_images"
    proc_dir = Path(output_dir).resolve() if output_dir else (base_data / "processed")

    logger.info("Initializing MedVision RetinaGuard Data Preparation Pipeline")
    logger.info("Project Root: %s", root)
    logger.info("Dataset Directory: %s", base_data)

    # 1. Load CSV
    records = load_aptos_csv(csv_file)
    logger.info("Loaded %d records from %s", len(records), csv_file)

    # 2. Match images
    matched_records = match_records_to_images(records, img_dir, project_root=root)

    # 3. Validate integrity
    report = validate_dataset(matched_records, img_dir, strict=True)
    logger.info("Dataset integrity validated: 0 missing files, 0 duplicate IDs, 0 empty images.")

    # 4. Stratified Split (Group-Aware by default to prevent data leakage)
    if group_aware:
        train_recs, val_recs = create_group_aware_stratified_split(
            matched_records,
            images_dir=img_dir,
            train_ratio=train_ratio,
            seed=seed,
            label_key="diagnosis",
        )
    else:
        train_recs, val_recs = create_stratified_split(
            matched_records,
            train_ratio=train_ratio,
            seed=seed,
            label_key="diagnosis",
        )

    # 5. Class Weights (computed strictly on training split)
    class_weights = compute_class_weights(train_recs, num_classes=5, method="balanced")

    # 6. Save Manifests
    train_path, val_path = save_manifests(train_recs, val_recs, proc_dir, project_root=root)

    # 7. Dataset Summary
    summary_path = proc_dir / "dataset_summary.json"
    summary = generate_dataset_summary(
        train_recs,
        val_recs,
        class_weights,
        output_json_path=summary_path,
        is_group_aware=group_aware,
    )

    return {
        "status": "SUCCESS",
        "train_manifest": str(train_path),
        "val_manifest": str(val_path),
        "summary_file": str(summary_path),
        "total_images": len(records),
        "train_count": len(train_recs),
        "val_count": len(val_recs),
        "class_distribution": report.class_distribution,
        "class_weights": class_weights,
        "summary": summary,
    }


class RetinaFundusDataset:
    """PyTorch Dataset adapter for streaming images directly from processed manifests.

    Streams images on-the-fly to prevent memory saturation.
    Applies RetinaImagePreprocessor transforms and returns (tensor, label, id_code).
    """

    def __init__(
        self,
        manifest_path: Union[Path, str],
        preprocessor: Any = None,
        project_root: Optional[Union[Path, str]] = None,
    ) -> None:
        """Initialize dataset from manifest file.

        Args:
            manifest_path: Path to train_manifest.csv or val_manifest.csv.
            preprocessor: RetinaImagePreprocessor instance.
            project_root: Root directory for resolving relative paths.
        """
        import torch

        self.manifest_path = Path(manifest_path).resolve()
        if not self.manifest_path.is_file():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        self.root = Path(project_root or find_project_root()).resolve()
        self.preprocessor = preprocessor

        self.records: List[Dict[str, Any]] = []
        with open(self.manifest_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                label_val = int(row.get("label") or row.get("diagnosis", 0))
                rel_path = row["image_path"]
                abs_path = (self.root / rel_path).resolve()
                self.records.append(
                    {
                        "id_code": row["id_code"],
                        "relative_path": rel_path,
                        "absolute_path": abs_path,
                        "label": label_val,
                    }
                )

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple[Any, Any]:
        """Fetch preprocessed image tensor and class label.

        Args:
            idx: Item index.

        Returns:
            Tuple of (torch.FloatTensor of shape (3, H, W), torch.LongTensor label).
        """
        import torch

        rec = self.records[idx]
        img_path = rec["absolute_path"]
        label = rec["label"]

        if self.preprocessor is not None:
            arr = self.preprocessor.preprocess(img_path)
            tensor = torch.from_numpy(arr).float()
        else:
            # Fallback direct read
            from PIL import Image
            with Image.open(img_path) as img:
                arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
                tensor = torch.from_numpy(arr).permute(2, 0, 1).float()

        target = torch.tensor(label, dtype=torch.long)
        return tensor, target


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = run_retina_data_pipeline()
    print("\n--- MEDVISION RETINAGUARD: DATA PREPARATION COMPLETE ---")
    print(f"Total Images: {result['total_images']}")
    print(f"Training Split: {result['train_count']} images (80%)")
    print(f"Validation Split: {result['val_count']} images (20%)")
    print("Class Weights:", result["class_weights"])
    print(f"Train Manifest: {result['train_manifest']}")
    print(f"Val Manifest: {result['val_manifest']}")

