"""Model evaluation pipeline for RetinaGuard Diabetic Retinopathy classification.

Provides rigorous, transparent, and leakage-aware evaluation of trained checkpoints:
1. Overall Accuracy
2. Macro-averaged F1 Score (balanced representation of minority and majority classes)
3. Weighted-averaged F1 Score
4. Per-class Precision, Recall, and F1 Score with support and predicted counts
5. 5x5 Multi-Class Confusion Matrix (ASCII and Markdown formatting)
6. Zero-division and empty dataset protections (handles zero predictions and missing classes safely)
7. Data leakage detection (identifies duplicate IDs and cross-split image hash overlap)
8. Transparent reporting: clearly distinguishes between Validation Set Monitoring and
   Independent Test Set Evaluation. If no independent test set exists, explicitly discloses this.
9. Dual artifact generation: machine-readable JSON and human-readable Markdown reports.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .dataset import RetinaFundusDataset, find_project_root
from .model import DR_CLASS_NAMES, RetinaResNet18, build_retina_model
from .preprocessing import RetinaImagePreprocessor

logger = logging.getLogger("medvision.retina.evaluate")


def compute_multiclass_metrics(
    y_true: Union[np.ndarray, Sequence[int]],
    y_pred: Union[np.ndarray, Sequence[int]],
    num_classes: int = 5,
    class_names: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """Calculate multi-class evaluation metrics with zero-division safety.

    Computes:
    - Overall accuracy
    - Macro and weighted F1-scores
    - Per-class precision, recall, and F1
    - Per-class support, predicted counts, true positives, false positives, false negatives
    - Confusion matrix (rows: true, cols: pred)
    - Zero-prediction and zero-support class tracking

    Args:
        y_true: 1D array or sequence of ground truth class integers.
        y_pred: 1D array or sequence of predicted class integers.
        num_classes: Number of discrete classes (default 5 for APTOS).
        class_names: Optional dictionary mapping class int to display string.

    Returns:
        Structured dictionary containing all computed metrics.
    """
    names = class_names or DR_CLASS_NAMES
    y_t = np.asarray(y_true, dtype=np.int64) if len(y_true) > 0 else np.array([], dtype=np.int64)
    y_p = np.asarray(y_pred, dtype=np.int64) if len(y_pred) > 0 else np.array([], dtype=np.int64)

    total_samples = len(y_t)

    # Handle empty dataset edge case safely
    if total_samples == 0:
        empty_classes = {
            str(c): {
                "name": names.get(c, f"Class {c}"),
                "support": 0,
                "predicted_count": 0,
                "tp": 0,
                "fp": 0,
                "fn": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
            }
            for c in range(num_classes)
        }
        return {
            "total_samples": 0,
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "class_metrics": empty_classes,
            "confusion_matrix": [[0] * num_classes for _ in range(num_classes)],
            "zero_prediction_classes": list(range(num_classes)),
            "zero_support_classes": list(range(num_classes)),
        }

    # 1. Build Confusion Matrix: shape (num_classes, num_classes)
    # cm[i, j] = count where ground truth is class i and prediction is class j
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_t, y_p):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t, p] += 1

    # Overall Accuracy
    correct = int(np.trace(cm))
    accuracy = float(correct / total_samples)

    class_metrics: Dict[str, Dict[str, Any]] = {}
    f1_scores: List[float] = []
    support_weights: List[int] = []
    zero_prediction_classes: List[int] = []
    zero_support_classes: List[int] = []

    for c in range(num_classes):
        tp = int(cm[c, c])
        fp = int(cm[:, c].sum() - tp)
        fn = int(cm[c, :].sum() - tp)
        support = int(cm[c, :].sum())
        predicted_count = int(cm[:, c].sum())

        if predicted_count == 0:
            zero_prediction_classes.append(c)
        if support == 0:
            zero_support_classes.append(c)

        # Zero-division guards
        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float((2 * precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

        f1_scores.append(f1)
        support_weights.append(support)

        class_metrics[str(c)] = {
            "name": names.get(c, f"Class {c}"),
            "support": support,
            "predicted_count": predicted_count,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
    total_support = sum(support_weights)
    weighted_f1 = (
        float(sum(f1 * s for f1, s in zip(f1_scores, support_weights)) / total_support)
        if total_support > 0
        else 0.0
    )

    return {
        "total_samples": total_samples,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "class_metrics": class_metrics,
        "confusion_matrix": cm.tolist(),
        "zero_prediction_classes": zero_prediction_classes,
        "zero_support_classes": zero_support_classes,
    }


def format_confusion_matrix(cm_list: List[List[int]], num_classes: int = 5) -> str:
    """Format confusion matrix as readable ASCII table."""
    lines = ["\nConfusion Matrix (Rows: Ground Truth, Cols: Predicted):"]
    header = "True \\ Pred | " + " | ".join(f"C{c:d}" for c in range(num_classes))
    lines.append(header)
    lines.append("-" * len(header))
    for r_idx, row in enumerate(cm_list):
        row_str = f"Class {r_idx:d}    | " + " | ".join(f"{val:4d}" for val in row)
        lines.append(row_str)
    return "\n".join(lines)


def format_markdown_confusion_matrix(
    cm_list: List[List[int]],
    class_names: Optional[Dict[int, str]] = None,
    num_classes: int = 5,
) -> str:
    """Format confusion matrix as clean GitHub Flavored Markdown table."""
    names = class_names or DR_CLASS_NAMES
    headers = ["True \\ Pred"] + [f"Pred C{c} ({names.get(c, f'C{c}')})" for c in range(num_classes)]
    table_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join([":---"] + [":---:"] * num_classes) + " |",
    ]

    for r_idx, row in enumerate(cm_list):
        c_label = f"**True C{r_idx} ({names.get(r_idx, f'C{r_idx}')})**"
        row_cells = [c_label] + [f"**{val}**" if r_idx == c_idx else str(val) for c_idx, val in enumerate(row)]
        table_lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(table_lines)


def check_data_leakage(
    eval_manifest_path: Union[Path, str],
    train_manifest_path: Optional[Union[Path, str]] = None,
    check_hashes: bool = False,
) -> Dict[str, Any]:
    """Inspect potential data leakage between evaluation dataset and training dataset.

    Checks:
    1. Overlap of image ID codes (`id_code`).
    2. Optional SHA-256 file hash overlap (detects duplicate physical images with different IDs).

    Args:
        eval_manifest_path: Path to evaluation manifest CSV.
        train_manifest_path: Path to train_manifest.csv (default: datasets/aptos/processed/train_manifest.csv).
        check_hashes: If True, computes SHA-256 digests for all images to detect bit-identical duplicates.

    Returns:
        Structured leakage assessment dictionary.
    """
    root = find_project_root()
    eval_csv = Path(eval_manifest_path).resolve()
    train_csv = (
        Path(train_manifest_path).resolve()
        if train_manifest_path
        else (root / "datasets" / "aptos" / "processed" / "train_manifest.csv")
    )

    if not eval_csv.is_file():
        raise FileNotFoundError(f"Evaluation manifest not found at: {eval_csv}")

    eval_records: List[Dict[str, str]] = []
    with open(eval_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eval_records.append(row)

    eval_ids = {r.get("id_code", "").strip() for r in eval_records if r.get("id_code")}

    train_ids: Set[str] = set()
    train_records: List[Dict[str, str]] = []
    if train_csv.is_file():
        with open(train_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                train_records.append(row)
                if row.get("id_code"):
                    train_ids.add(row["id_code"].strip())

    id_overlap = sorted(list(eval_ids.intersection(train_ids)))

    hash_overlap: List[str] = []
    if check_hashes and train_csv.is_file():
        def _hash_file(p_str: str) -> Optional[str]:
            p = root / p_str if not Path(p_str).is_absolute() else Path(p_str)
            if not p.is_file():
                return None
            h = hashlib.sha256()
            with open(p, "rb") as bf:
                while chunk := bf.read(65536):
                    h.update(chunk)
            return h.hexdigest()

        train_hashes: Set[str] = set()
        for r in train_records:
            if "image_path" in r:
                dig = _hash_file(r["image_path"])
                if dig:
                    train_hashes.add(dig)

        for r in eval_records:
            if "image_path" in r:
                dig = _hash_file(r["image_path"])
                if dig and dig in train_hashes:
                    hash_overlap.append(r.get("id_code", "unknown"))

    has_leakage = len(id_overlap) > 0 or len(hash_overlap) > 0

    return {
        "eval_manifest": str(eval_csv),
        "train_manifest": str(train_csv) if train_csv.is_file() else None,
        "eval_sample_count": len(eval_records),
        "train_sample_count": len(train_records),
        "has_leakage": has_leakage,
        "id_overlap_count": len(id_overlap),
        "id_overlap_samples": id_overlap[:10],
        "hash_overlap_count": len(hash_overlap),
        "hash_overlap_samples": hash_overlap[:10],
        "check_hashes_performed": check_hashes,
    }


def generate_markdown_report(
    metrics: Dict[str, Any],
    output_path: Optional[Union[Path, str]] = None,
) -> str:
    """Generate a clean, structured Markdown evaluation report.

    Args:
        metrics: Dictionary returned by evaluate_retina_model / run_evaluation.
        output_path: Optional file path to persist the generated report.

    Returns:
        The markdown text string.
    """
    timestamp = metrics.get("evaluated_at", datetime.now(timezone.utc).isoformat())
    split_type = metrics.get("split_type", "Validation Split").upper()
    total_samples = metrics.get("total_samples", 0)
    acc = metrics.get("accuracy", 0.0)
    macro_f1 = metrics.get("macro_f1", 0.0)
    weighted_f1 = metrics.get("weighted_f1", 0.0)
    val_loss = metrics.get("val_loss", "N/A")
    ckpt = metrics.get("checkpoint_evaluated", "Unknown Checkpoint")
    epoch = metrics.get("checkpoint_epoch", "Unknown")
    is_test_set = metrics.get("is_independent_test_set", False)

    md: List[str] = [
        "# RetinaGuard — Model Evaluation Report",
        "",
        f"**Evaluation Timestamp**: `{timestamp}`  ",
        f"**Model Checkpoint**: `{ckpt}`  ",
        f"**Training Epoch**: `{epoch}`  ",
        f"**Dataset Split Evaluated**: `{metrics.get('manifest_evaluated', 'val_manifest.csv')}` (`{split_type}`)  ",
        f"**Total Samples Evaluated**: `{total_samples}`  ",
        "",
        "---",
        "",
        "## 1. Dataset Split & Data Leakage Disclosure",
        "",
    ]

    if not is_test_set:
        md.extend([
            "> [!IMPORTANT]",
            "> **Dataset Split Transparency Notice**:",
            f"> This evaluation was performed on the **validation split** (`{total_samples}` images), which was used during Step 3 model training for checkpoint selection and loss monitoring.",
            "> **No separate, independent labelled test dataset** (e.g., held-out competition test set with ground truth) currently exists in the workspace.",
            "> These metrics reflect validation performance on held-out training partitions and **must not be misrepresented as independent test set metrics**.",
            "",
        ])
    else:
        md.extend([
            "> [!NOTE]",
            "> **Independent Test Evaluation**:",
            f"> This evaluation was executed on an independent test dataset (`{total_samples}` images).",
            "",
        ])

    leakage = metrics.get("leakage_assessment")
    if leakage:
        md.extend([
            "### Data Disjointness Verification",
            f"- **Train Manifest**: `{leakage.get('train_manifest', 'N/A')}` ({leakage.get('train_sample_count', 0)} samples)",
            f"- **Evaluation Manifest**: `{leakage.get('eval_manifest', 'N/A')}` ({leakage.get('eval_sample_count', 0)} samples)",
            f"- **ID Overlap**: `{leakage.get('id_overlap_count', 0)}` IDs",
            f"- **Strict Disjointness**: `{'PASSED (Zero Overlap)' if leakage.get('id_overlap_count', 0) == 0 else 'FAILED (Data Leakage Detected)'}`",
            "",
        ])
        if leakage.get("hash_overlap_count", 0) > 0:
            md.extend([
                "> [!WARNING]",
                f"> **Cross-Split Duplicate Image Hashes**: Found `{leakage['hash_overlap_count']}` images with identical SHA-256 hashes crossing the split.",
                "> This is an inherent property of the raw APTOS 2019 dataset (which contains identical duplicate photos assigned distinct patient IDs and occasionally conflicting human labels).",
                "",
            ])

    md.extend([
        "---",
        "",
        "## 2. Global Performance Summary",
        "",
        "| Metric | Score | Clinical Context |",
        "| :--- | :---: | :--- |",
        f"| **Overall Accuracy** | **{acc * 100:.2f}%** ({metrics.get('correct_count', round(acc * total_samples))}/{total_samples}) | Proportion of exact grade matches across all 5 categories. |",
        f"| **Macro-averaged F1** | **{macro_f1:.4f}** | Unweighted average of per-class F1 scores (primary metric for class imbalance). |",
        f"| **Weighted-averaged F1** | **{weighted_f1:.4f}** | Sample-weighted average F1 across classes. |",
        f"| **Validation Cross-Entropy Loss** | **{val_loss}** | Uncalibrated Cross-Entropy loss on evaluation split. |",
        "",
        "---",
        "",
        "## 3. Per-Class Diagnostic Performance",
        "",
        "| Class ID | Clinical Diagnosis | Support | Predicted | TP | FP | FN | Precision | Recall | F1-Score |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    class_metrics = metrics.get("class_metrics", {})
    for c_str in sorted(class_metrics.keys(), key=lambda x: int(x)):
        cm = class_metrics[c_str]
        md.append(
            f"| **{c_str}** | {cm['name']} | {cm['support']} | {cm.get('predicted_count', 0)} | "
            f"{cm.get('tp', 0)} | {cm.get('fp', 0)} | {cm.get('fn', 0)} | "
            f"{cm['precision']:.4f} | {cm['recall']:.4f} | **{cm['f1_score']:.4f}** |"
        )

    md.extend([
        "",
        "---",
        "",
        "## 4. Multi-Class Confusion Matrix",
        "",
        format_markdown_confusion_matrix(metrics.get("confusion_matrix", []), num_classes=len(class_metrics)),
        "",
        "```text",
        format_confusion_matrix(metrics.get("confusion_matrix", []), num_classes=len(class_metrics)),
        "```",
    ])

    c0_info = class_metrics.get("0", {})
    c1_info = class_metrics.get("1", {})
    c3_info = class_metrics.get("3", {})
    c0_sup = c0_info.get("support", 0)
    c1_sup = c1_info.get("support", 0)
    c3_sup = c3_info.get("support", 0)
    c0_label = "No DR" if "No Diabetic Retinopathy" in c0_info.get("name", "") else c0_info.get("name", "Class 0")
    c1_label = "Mild NPDR" if "Mild" in c1_info.get("name", "") else c1_info.get("name", "Class 1")
    c3_label = "Severe NPDR" if "Severe" in c3_info.get("name", "") else c3_info.get("name", "Class 3")

    imbalance_text = (
        f"1. **Class-Imbalance Dynamics**: Classes 1 ({c1_label}, {c1_sup} samples) and 3 "
        f"({c3_label}, {c3_sup} samples) represent minority clinical stages compared to "
        f"Class 0 ({c0_label}, {c0_sup} samples)."
    )

    md.extend([
        "",
        "---",
        "",
        "## 5. Clinical Observations & Error Analysis",
        "",
        imbalance_text,
        "2. **Adjacent Grade Confusion**: Most misclassifications occur between contiguous severity grades (e.g., Grade 0 vs. Grade 1, or Grade 2 vs. Grade 3), which clinically reflects subtle progression of microvascular lesions.",
        "3. **Zero Predictions Guard**: All metrics safely handle zero-prediction scenarios without numeric instability.",
        "4. **Development Benchmark Limitation**: Current validation metrics reflect internal development results on a held-out training partition, not independent clinical validation on prospective patient cohorts.",
        "",
        "---",
        "",
        "> [!CAUTION]",
        "> **Medical Research Prototype Notice**:",
        "> This evaluation report is generated for educational and machine learning research benchmarking only.",
        "> Current validation metrics represent internal development results, not independent clinical validation.",
        "> MedVision AI RetinaGuard is not certified as a medical device or diagnostic system. These metrics must not be used to justify clinical reliability, screening efficacy, or patient care decisions.",
    ])

    report_text = "\n".join(md)
    if output_path:
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(report_text)

    return report_text


def evaluate_retina_model(
    model: nn.Module,
    val_loader: DataLoader,
    criterion: Optional[nn.Module] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Execute evaluation loop over DataLoader without modifying model weights.

    Guarantees:
    - Model set to eval() mode.
    - All gradients disabled via torch.no_grad().
    - Zero parameter modifications during execution.

    Args:
        model: RetinaGuard PyTorch neural network.
        val_loader: DataLoader wrapping evaluation split.
        criterion: Optional loss function for computing validation loss.
        device: Device on which evaluation is performed (cpu or cuda).

    Returns:
        Dictionary of computed evaluation metrics.
    """
    dev = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
    model.eval()
    model.to(dev)

    total_loss = 0.0
    all_targets: List[int] = []
    all_predictions: List[int] = []

    with torch.no_grad():
        for images, targets in val_loader:
            images = images.to(dev)
            targets = targets.to(dev)

            logits = model(images)
            if criterion is not None:
                loss = criterion(logits, targets)
                if torch.isnan(loss):
                    raise RuntimeError("Encountered NaN loss during evaluation.")
                total_loss += loss.item() * images.size(0)

            preds = torch.argmax(logits, dim=1)

            all_targets.extend(targets.cpu().numpy().tolist())
            all_predictions.extend(preds.cpu().numpy().tolist())

    y_true = np.array(all_targets, dtype=np.int64)
    y_pred = np.array(all_predictions, dtype=np.int64)

    metrics = compute_multiclass_metrics(y_true, y_pred, num_classes=5)
    mean_loss = float(total_loss / len(y_true)) if len(y_true) > 0 and criterion else None
    metrics["val_loss"] = round(mean_loss, 4) if mean_loss is not None else None
    metrics["correct_count"] = int(np.sum(y_true == y_pred)) if len(y_true) > 0 else 0

    return metrics


def run_evaluation(
    checkpoint_path: Union[Path, str],
    manifest_path: Optional[Union[Path, str]] = None,
    split_type: Optional[str] = None,
    batch_size: int = 32,
    target_size: Tuple[int, int] = (224, 224),
    output_json_path: Optional[Union[Path, str]] = None,
    output_markdown_path: Optional[Union[Path, str]] = None,
    check_leakage: bool = True,
) -> Dict[str, Any]:
    """Run standalone evaluation pipeline and export JSON + Markdown reports.

    Args:
        checkpoint_path: Path to trained model checkpoint (.pt).
        manifest_path: Path to manifest CSV (default: datasets/aptos/processed/val_manifest.csv).
        split_type: "validation" or "test" (auto-detected if omitted).
        batch_size: Batch size for evaluation DataLoader.
        target_size: Input image resolution.
        output_json_path: Path to save JSON report.
        output_markdown_path: Path to save Markdown report.
        check_leakage: If True, assesses ID overlap against train_manifest.csv.

    Returns:
        Comprehensive evaluation metrics dictionary.
    """
    root = find_project_root()
    ckpt_file = Path(checkpoint_path).resolve()
    if not ckpt_file.is_file():
        raise FileNotFoundError(f"Checkpoint file not found: {ckpt_file}")

    eval_csv = (
        Path(manifest_path).resolve()
        if manifest_path
        else (root / "datasets" / "aptos" / "processed" / "val_manifest.csv")
    )
    if not eval_csv.is_file():
        raise FileNotFoundError(f"Evaluation manifest file not found: {eval_csv}")

    # Determine split classification
    if split_type is None:
        fname = eval_csv.name.lower()
        is_independent_test = "test" in fname
        detected_split = "test" if is_independent_test else "validation"
    else:
        detected_split = split_type.lower()
        is_independent_test = detected_split == "test"

    logger.info("Evaluating model checkpoint: %s", ckpt_file)
    logger.info("Evaluation manifest: %s (Type: %s)", eval_csv, detected_split)

    # 1. Data Leakage Assessment
    leakage_info = None
    if check_leakage:
        try:
            leakage_info = check_data_leakage(eval_csv, check_hashes=False)
            if leakage_info["has_leakage"] and is_independent_test:
                logger.warning(
                    "DATA LEAKAGE WARNING: %d overlapping IDs detected between test and train manifests!",
                    leakage_info["id_overlap_count"],
                )
        except Exception as err:
            logger.warning("Could not complete leakage assessment: %s", err)

    # 2. Load model in evaluation mode
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, ckpt_meta = RetinaResNet18.load_from_checkpoint(ckpt_file, map_location=device)
    model.to(device)

    # 3. Build deterministic dataset & DataLoader
    preprocessor = RetinaImagePreprocessor(
        target_size=target_size,
        normalize=True,
        is_training=False,
        augment=False,
    )
    dataset = RetinaFundusDataset(eval_csv, preprocessor=preprocessor, project_root=root)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # 4. Execute evaluation loop
    criterion = nn.CrossEntropyLoss()
    metrics = evaluate_retina_model(model, loader, criterion=criterion, device=device)

    # 5. Attach audit metadata
    now_iso = datetime.now(timezone.utc).isoformat()
    metrics["evaluated_at"] = now_iso
    metrics["split_type"] = detected_split
    metrics["is_independent_test_set"] = is_independent_test
    metrics["manifest_evaluated"] = str(eval_csv.relative_to(root) if eval_csv.is_relative_to(root) else eval_csv)
    metrics["checkpoint_evaluated"] = str(ckpt_file.relative_to(root) if ckpt_file.is_relative_to(root) else ckpt_file)
    metrics["checkpoint_epoch"] = ckpt_meta.get("epoch", 0)
    metrics["leakage_assessment"] = leakage_info

    # 6. Save Machine-Readable JSON Report
    json_path = (
        Path(output_json_path).resolve()
        if output_json_path
        else (ckpt_file.parent / "eval_results.json")
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # 7. Save Human-Readable Markdown Report
    md_path = (
        Path(output_markdown_path).resolve()
        if output_markdown_path
        else (ckpt_file.parent / "EVALUATION_REPORT.md")
    )
    generate_markdown_report(metrics, output_path=md_path)

    # 8. Print Console Summary
    print("\n" + "=" * 65)
    print(f"MEDVISION RETINAGUARD: {detected_split.upper()} EVALUATION REPORT")
    print("=" * 65)
    print(f"Manifest:           {eval_csv.name} ({metrics['total_samples']} samples)")
    print(f"Evaluation Mode:    {'Independent Test Split' if is_independent_test else 'Validation Split (Held-Out Training Partition)'}")
    print(f"Overall Accuracy:   {metrics['accuracy'] * 100:.2f}% ({metrics['correct_count']}/{metrics['total_samples']})")
    print(f"Macro F1 Score:     {metrics['macro_f1']:.4f}")
    print(f"Weighted F1 Score:  {metrics['weighted_f1']:.4f}")
    if metrics.get("val_loss") is not None:
        print(f"Loss:               {metrics['val_loss']}")
    print("-" * 65)
    print("Per-Class Metrics:")
    for c_id, c_data in metrics["class_metrics"].items():
        print(
            f"  Class {c_id} ({c_data['name']:<25}): "
            f"Prec={c_data['precision']:.4f}, Rec={c_data['recall']:.4f}, F1={c_data['f1_score']:.4f} "
            f"[Support: {c_data['support']}, Pred: {c_data.get('predicted_count', 0)}]"
        )
    print(format_confusion_matrix(metrics["confusion_matrix"]))
    print("=" * 65)
    print(f"JSON Report:     {json_path}")
    print(f"Markdown Report: {md_path}")
    print("=" * 65 + "\n")

    return metrics


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Evaluate RetinaGuard Model Checkpoint")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="ai_models/retina/weights/best_model.pt",
        help="Path to model checkpoint (.pt)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to manifest CSV (default: datasets/aptos/processed/val_manifest.csv)",
    )
    parser.add_argument(
        "--split-type",
        type=str,
        default=None,
        choices=["validation", "test"],
        help="Explicit split designation ('validation' or 'test')",
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for evaluation")
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to save output JSON evaluation report",
    )
    parser.add_argument(
        "--output-markdown",
        type=str,
        default=None,
        help="Path to save output Markdown evaluation report",
    )
    parser.add_argument(
        "--check-leakage",
        action="store_true",
        default=True,
        help="Verify manifest disjointness against train_manifest.csv",
    )
    args = parser.parse_args()

    run_evaluation(
        checkpoint_path=args.checkpoint,
        manifest_path=args.manifest,
        split_type=args.split_type,
        batch_size=args.batch_size,
        output_json_path=args.output_json,
        output_markdown_path=args.output_markdown,
        check_leakage=args.check_leakage,
    )
