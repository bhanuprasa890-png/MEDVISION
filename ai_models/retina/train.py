"""Training pipeline for RetinaGuard Diabetic Retinopathy classification.

Implements transfer learning with ResNet-18:
1. Loads pre-generated, stratified manifests (train_manifest.csv, val_manifest.csv).
2. Class-imbalance mitigation using balanced class-weighted Cross-Entropy loss.
3. Two-phase transfer learning:
   - Phase 1: Train classification head with frozen backbone to preserve pretrained features.
   - Phase 2: Fine-tune full network with differential learning rates and cosine annealing.
4. Memory-efficient on-the-fly streaming via PyTorch Dataset / DataLoader.
5. Reproducibility enforcement using fixed random seeds.
6. Checkpoint management tracking the best validation Macro F1 score.
7. Support for training resumption and lightweight smoke testing.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .dataset import RetinaFundusDataset, compute_class_weights, find_project_root
from .evaluate import compute_multiclass_metrics, evaluate_retina_model, format_confusion_matrix
from .model import DR_CLASS_NAMES, RetinaResNet18, build_retina_model
from .preprocessing import RetinaImagePreprocessor

logger = logging.getLogger("medvision.retina.train")

PROTECTED_CHECKPOINTS = {
    "best_model.pt",
    "best_model_backup.pt",
    "best_model_epoch1_verified_backup.pt",
    "retinaguard_v2_epoch2_verified_backup.pt",
}


def validate_checkpoint_safety(output_dir: Union[Path, str], filename: str, is_resuming: bool = False) -> None:
    """Ensure training never overwrites historical baseline checkpoints or verified backups.

    Args:
        output_dir: Output directory where checkpoints are saved.
        filename: Target filename for best model checkpoint.
        is_resuming: Whether trainer is executing a resumed training run.

    Raises:
        ValueError: If filename conflicts with a protected baseline or backup file.
    """
    clean_name = Path(filename).name
    out_dir_path = Path(output_dir).resolve()
    target_path = out_dir_path / clean_name

    # Check if target name matches a backup naming pattern
    if clean_name.endswith(("_verified_backup.pt", "_backup.pt")):
        raise ValueError(
            f"Target checkpoint filename '{clean_name}' cannot be a backup filename. "
            f"Please choose an active run filename such as 'retinaguard_v2.pt'."
        )

    # Check if target matches canonical project baseline
    try:
        project_baseline = (find_project_root() / "ai_models" / "retina" / "weights" / "best_model.pt").resolve()
        if target_path == project_baseline:
            raise ValueError(
                "Overwriting project baseline 'best_model.pt' in ai_models/retina/weights is forbidden "
                "to preserve benchmark evaluations. Specify --checkpoint-name retinaguard_v2.pt (or a custom name)."
            )
    except Exception:
        pass

    # If resuming, strictly forbid targeting best_model.pt anywhere
    if is_resuming and clean_name == "best_model.pt":
        raise ValueError(
            "Cannot resume training into 'best_model.pt'. "
            "Please specify --checkpoint-name retinaguard_v2.pt to preserve baseline weights."
        )


def set_seed(seed: int = 42) -> None:
    """Set random seed across all libraries for deterministic execution."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class RetinaTrainer:
    """Orchestrates model training, validation, checkpointing, and logging."""

    def __init__(
        self,
        model: RetinaResNet18,
        train_loader: DataLoader,
        val_loader: DataLoader,
        class_weights: Optional[Sequence[float]] = None,
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-2,
        output_dir: Union[Path, str] = "ai_models/retina/weights",
        device: Optional[torch.device] = None,
        max_batches_per_epoch: Optional[int] = None,
        resume_checkpoint: Optional[Union[Path, str]] = None,
        freeze_backbone_epochs: int = 1,
    ) -> None:
        """Initialize trainer.

        Args:
            model: RetinaResNet18 instance.
            train_loader: Training split DataLoader.
            val_loader: Validation split DataLoader.
            class_weights: Balanced class weights sequence of length 5.
            learning_rate: Base learning rate.
            weight_decay: L2 regularization penalty.
            output_dir: Directory where checkpoints and logs are saved.
            device: Torch execution device.
            max_batches_per_epoch: Optional limit on batches per epoch for quick validation.
            resume_checkpoint: Optional path to a checkpoint (.pt) to safely resume from.
            freeze_backbone_epochs: Number of initial epochs with frozen backbone.
        """
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.max_batches_per_epoch = max_batches_per_epoch
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.freeze_backbone_epochs = freeze_backbone_epochs

        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Class-Weighted Loss Function
        if class_weights is not None:
            weight_tensor = torch.tensor(class_weights, dtype=torch.float32, device=self.device)
            self.criterion = nn.CrossEntropyLoss(weight=weight_tensor)
            logger.info("Using class-weighted CrossEntropyLoss: %s", [round(w, 4) for w in class_weights])
        else:
            self.criterion = nn.CrossEntropyLoss()

        self.scheduler: Optional[torch.optim.lr_scheduler.LRScheduler] = None
        self.best_macro_f1 = -1.0
        self.start_epoch = 1
        self.history: List[Dict[str, Any]] = []
        self.resumed_from: Optional[Path] = None
        self._resumed_in_phase2 = False
        self._resumed_scheduler_state: Optional[Dict[str, Any]] = None

        if resume_checkpoint is not None:
            ckpt_path = Path(resume_checkpoint).resolve()
            if not ckpt_path.is_file():
                raise FileNotFoundError(f"Resume checkpoint file not found: {ckpt_path}")

            logger.info("Loading checkpoint for resumption: %s", ckpt_path)
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            self.resumed_from = ckpt_path

            # Restore model weights
            if "state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["state_dict"])
            else:
                self.model.load_state_dict(checkpoint)

            completed_epoch = int(checkpoint.get("epoch", 0))
            self.start_epoch = completed_epoch + 1
            self.best_macro_f1 = float(checkpoint.get("val_macro_f1", -1.0))
            val_loss = float(checkpoint.get("val_loss", 0.0))

            logger.info(
                "Resuming training: Completed epoch %d -> Next epoch %d | Best Macro F1: %.4f | Val Loss: %.4f",
                completed_epoch,
                self.start_epoch,
                self.best_macro_f1,
                val_loss,
            )

            # Phase and Optimizer restoration
            if completed_epoch >= self.freeze_backbone_epochs:
                logger.info(
                    "Checkpoint completed epoch (%d) >= freeze_backbone_epochs (%d): Configuring Phase 2 fine-tuning.",
                    completed_epoch,
                    self.freeze_backbone_epochs,
                )
                self.model.set_backbone_trainable(True)
                self.optimizer = torch.optim.AdamW(
                    [
                        {"params": self.model.backbone.layer4.parameters(), "lr": self.learning_rate * 0.5},
                        {"params": self.model.backbone.fc.parameters(), "lr": self.learning_rate},
                    ],
                    weight_decay=self.weight_decay,
                )
                self._resumed_in_phase2 = True
            else:
                logger.info(
                    "Checkpoint completed epoch (%d) < freeze_backbone_epochs (%d): Retaining Phase 1 frozen backbone.",
                    completed_epoch,
                    self.freeze_backbone_epochs,
                )
                self.model.set_backbone_trainable(False)
                self.optimizer = torch.optim.AdamW(
                    filter(lambda p: p.requires_grad, self.model.parameters()),
                    lr=self.learning_rate,
                    weight_decay=self.weight_decay,
                )
                self._resumed_in_phase2 = False

            # Restore optimizer state
            if "optimizer_state" in checkpoint and checkpoint["optimizer_state"] is not None:
                self.optimizer.load_state_dict(checkpoint["optimizer_state"])
                logger.info("Restored optimizer state successfully (parameter groups: %d).", len(self.optimizer.param_groups))

            # Ensure initial_lr exists on all parameter groups
            default_lrs = [self.learning_rate * 0.5, self.learning_rate] if self._resumed_in_phase2 else [self.learning_rate]
            for i, group in enumerate(self.optimizer.param_groups):
                if "initial_lr" not in group:
                    fallback_lr = default_lrs[i] if i < len(default_lrs) else group.get("lr", self.learning_rate)
                    group["initial_lr"] = fallback_lr

            # Record scheduler state if available
            if "scheduler_state" in checkpoint and checkpoint["scheduler_state"] is not None:
                self._resumed_scheduler_state = checkpoint["scheduler_state"]
                logger.info("Found explicit scheduler_state in checkpoint.")
            else:
                self._resumed_scheduler_state = None
                logger.info("No explicit 'scheduler_state' found in checkpoint (will be reconstructed upon training start).")
        else:
            # Standard initial Phase 1 optimizer
            self.optimizer = torch.optim.AdamW(
                filter(lambda p: p.requires_grad, self.model.parameters()),
                lr=self.learning_rate,
                weight_decay=self.weight_decay,
            )

    def train_epoch(self, epoch: int) -> Tuple[float, float]:
        """Execute a single training epoch.

        Args:
            epoch: Current epoch index.

        Returns:
            Tuple of (mean_train_loss, train_accuracy).
        """
        self.model.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        batch_count = 0
        start_time = time.time()

        for batch_idx, (images, targets) in enumerate(self.train_loader):
            if self.max_batches_per_epoch and batch_idx >= self.max_batches_per_epoch:
                break

            images = images.to(self.device)
            targets = targets.to(self.device)

            self.optimizer.zero_grad()
            logits = self.model(images)
            loss = self.criterion(logits, targets)

            if torch.isnan(loss):
                raise RuntimeError(f"NaN loss encountered at epoch {epoch}, batch {batch_idx}")

            loss.backward()
            # Gradient clipping to prevent gradient explosion
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=2.0)
            self.optimizer.step()

            batch_size = images.size(0)
            total_loss += loss.item() * batch_size
            preds = torch.argmax(logits, dim=1)
            total_correct += int((preds == targets).sum().item())
            total_samples += batch_size
            batch_count += 1

            if batch_count % 20 == 0 or batch_count == len(self.train_loader):
                logger.info(
                    "Epoch [%d] Batch [%d/%d] - Loss: %.4f - Running Acc: %.2f%%",
                    epoch,
                    batch_count,
                    len(self.train_loader) if not self.max_batches_per_epoch else self.max_batches_per_epoch,
                    loss.item(),
                    (total_correct / total_samples) * 100,
                )

        elapsed = time.time() - start_time
        mean_loss = total_loss / total_samples if total_samples > 0 else 0.0
        acc = (total_correct / total_samples) if total_samples > 0 else 0.0

        logger.info(
            "Epoch [%d] Training Complete in %.1fs - Loss: %.4f - Accuracy: %.2f%%",
            epoch,
            elapsed,
            mean_loss,
            acc * 100,
        )
        return mean_loss, acc

    def train(
        self,
        total_epochs: int = 10,
        freeze_backbone_epochs: Optional[int] = None,
        best_checkpoint_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute full training lifecycle with validation and checkpoint saving.

        Args:
            total_epochs: Total number of training epochs (default: 10).
            freeze_backbone_epochs: Number of initial epochs with frozen backbone (defaults to instance setting).
            best_checkpoint_filename: Filename for saving best checkpoint. Defaults to 'retinaguard_v2.pt'
                                      when resuming, and 'best_model.pt' for non-resumed training in custom directories.

        Returns:
            Dictionary containing final training metrics and best checkpoint path.
        """
        freeze_epochs = freeze_backbone_epochs if freeze_backbone_epochs is not None else self.freeze_backbone_epochs

        # Resolve target filename
        if best_checkpoint_filename is None:
            target_filename = "retinaguard_v2.pt" if (self.resumed_from is not None) else "best_model.pt"
        else:
            target_filename = best_checkpoint_filename

        # Enforce checkpoint safety against baseline corruption
        validate_checkpoint_safety(
            self.output_dir,
            target_filename,
            is_resuming=(self.resumed_from is not None),
        )

        if self.start_epoch > total_epochs:
            raise ValueError(
                f"Cannot resume training: checkpoint completed epoch is {self.start_epoch - 1}, "
                f"which is >= requested total_epochs {total_epochs}. Set total_epochs to at least {self.start_epoch}."
            )

        logger.info(
            "Starting/Resuming RetinaGuard training on %s (start_epoch=%d, total_epochs=%d, freeze_epochs=%d)",
            self.device,
            self.start_epoch,
            total_epochs,
            freeze_epochs,
        )

        # Scheduler configuration & restoration
        if self._resumed_in_phase2 or (self.start_epoch > freeze_epochs):
            phase2_total_steps = max(1, total_epochs - freeze_epochs)
            completed_phase2_steps = (self.start_epoch - 1) - freeze_epochs

            if self._resumed_scheduler_state is not None:
                self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    self.optimizer, T_max=phase2_total_steps, eta_min=0
                )
                self.scheduler.load_state_dict(self._resumed_scheduler_state)
                logger.info("Restored explicit scheduler state from checkpoint.")
            else:
                logger.info(
                    "Scheduler restoration notice: Checkpoint does not contain explicit 'scheduler_state'. "
                    "Reconstructing CosineAnnealingLR schedule from Phase 2 configuration "
                    "(T_max=%d, catching up %d completed step(s)).",
                    phase2_total_steps,
                    completed_phase2_steps,
                )
                # Reset lr in param_groups to initial_lr so CosineAnnealingLR base_lrs match original definition
                for group in self.optimizer.param_groups:
                    group["lr"] = group.get("initial_lr", group["lr"])

                self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    self.optimizer, T_max=phase2_total_steps, eta_min=0
                )
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    for _ in range(completed_phase2_steps):
                        self.scheduler.step()

                logger.info(
                    "CosineAnnealingLR schedule aligned for next epoch %d (%d/%d steps), current lrs: %s",
                    self.start_epoch,
                    completed_phase2_steps + 1,
                    phase2_total_steps,
                    [round(g["lr"], 8) for g in self.optimizer.param_groups],
                )
        else:
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=max(1, total_epochs - freeze_epochs)
            )
            if self._resumed_scheduler_state is not None:
                self.scheduler.load_state_dict(self._resumed_scheduler_state)

        best_checkpoint_path = self.output_dir / target_filename
        latest_checkpoint_path = self.output_dir / "checkpoint_latest.pt"

        # Checkpoint Preservation: If target checkpoint file already exists, create safety backup
        if best_checkpoint_path.is_file():
            backup_path = self.output_dir / f"{best_checkpoint_path.stem}_backup{best_checkpoint_path.suffix}"
            try:
                import shutil
                shutil.copy2(best_checkpoint_path, backup_path)
                logger.info(
                    "Checkpoint preservation active: Backed up existing checkpoint %s to %s",
                    best_checkpoint_path.name,
                    backup_path.name,
                )
            except OSError as err:
                logger.warning("Could not backup existing checkpoint: %s", err)

        total_start_time = time.time()

        for epoch in range(self.start_epoch, total_epochs + 1):
            # Phase management: unfreeze backbone after initial head alignment (if not already in Phase 2)
            if epoch == freeze_epochs + 1 and not self._resumed_in_phase2:
                logger.info("Unfreezing ResNet-18 backbone conv layers for fine-tuning.")
                self.model.set_backbone_trainable(True)
                # Re-initialize optimizer with differential learning rate
                self.optimizer = torch.optim.AdamW(
                    [
                        {"params": self.model.backbone.layer4.parameters(), "lr": self.learning_rate * 0.5},
                        {"params": self.model.backbone.fc.parameters(), "lr": self.learning_rate},
                    ],
                    weight_decay=self.weight_decay,
                )
                self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    self.optimizer, T_max=total_epochs - freeze_epochs
                )

            epoch_start = time.time()
            train_loss, train_acc = self.train_epoch(epoch)

            # Validation evaluation
            val_metrics = evaluate_retina_model(
                self.model,
                self.val_loader,
                criterion=self.criterion,
                device=self.device,
            )

            if self.scheduler is not None:
                self.scheduler.step()

            val_macro_f1 = val_metrics["macro_f1"]
            val_loss = val_metrics["val_loss"] or 0.0
            val_acc = val_metrics["accuracy"]
            epoch_duration = time.time() - epoch_start

            epoch_record = {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "train_accuracy": round(train_acc, 4),
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "val_macro_f1": round(val_macro_f1, 4),
                "duration_seconds": round(epoch_duration, 1),
            }
            self.history.append(epoch_record)

            logger.info(
                "Epoch [%d/%d] Val Loss: %.4f | Val Acc: %.2f%% | Val Macro F1: %.4f",
                epoch,
                total_epochs,
                val_loss,
                val_acc * 100,
                val_macro_f1,
            )

            # Save latest checkpoint for resumption support
            self.model.save_checkpoint(
                latest_checkpoint_path,
                epoch=epoch,
                val_macro_f1=val_macro_f1,
                val_loss=val_loss,
                optimizer_state=self.optimizer.state_dict(),
                scheduler_state=self.scheduler.state_dict() if self.scheduler is not None else None,
                config={
                    "total_epochs": total_epochs,
                    "freeze_backbone_epochs": freeze_epochs,
                    "learning_rate": self.learning_rate,
                    "weight_decay": self.weight_decay,
                },
            )

            # Checkpoint best model based on validation macro F1
            if val_macro_f1 > self.best_macro_f1:
                old_f1 = self.best_macro_f1
                self.best_macro_f1 = val_macro_f1
                logger.info(
                    "--> NEW BEST VALIDATION MACRO F1: %.4f (previous best: %.4f). Saving to %s",
                    val_macro_f1,
                    old_f1,
                    best_checkpoint_path,
                )
                self.model.save_checkpoint(
                    best_checkpoint_path,
                    epoch=epoch,
                    val_macro_f1=val_macro_f1,
                    val_loss=val_loss,
                    optimizer_state=self.optimizer.state_dict(),
                    scheduler_state=self.scheduler.state_dict() if self.scheduler is not None else None,
                    config={
                        "total_epochs": total_epochs,
                        "freeze_backbone_epochs": freeze_epochs,
                        "learning_rate": self.learning_rate,
                        "weight_decay": self.weight_decay,
                    },
                )

        total_runtime = time.time() - total_start_time

        # Save complete training logs
        log_file = self.output_dir / "training_log.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_epochs": total_epochs,
                    "best_macro_f1": round(self.best_macro_f1, 4),
                    "total_runtime_seconds": round(total_runtime, 1),
                    "device": str(self.device),
                    "history": self.history,
                },
                f,
                indent=2,
            )

        return {
            "status": "COMPLETED",
            "best_checkpoint": str(best_checkpoint_path),
            "latest_checkpoint": str(latest_checkpoint_path),
            "best_macro_f1": self.best_macro_f1,
            "total_runtime_seconds": total_runtime,
            "history": self.history,
        }


def train_retinaguard(
    train_manifest: Optional[Union[Path, str]] = None,
    val_manifest: Optional[Union[Path, str]] = None,
    output_dir: Optional[Union[Path, str]] = None,
    epochs: int = 10,
    batch_size: int = 16,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-2,
    target_size: Tuple[int, int] = (224, 224),
    seed: int = 42,
    smoke_test: bool = False,
    max_batches: Optional[int] = None,
    checkpoint_name: Optional[str] = None,
    resume_path: Optional[Union[Path, str]] = None,
) -> Dict[str, Any]:
    """Top-level entry point to train or resume RetinaGuard.

    Args:
        train_manifest: Path to train_manifest.csv.
        val_manifest: Path to val_manifest.csv.
        output_dir: Directory to save model checkpoints.
        epochs: Number of training epochs (default: 10).
        batch_size: Batch size for training.
        learning_rate: Learning rate for AdamW.
        weight_decay: L2 penalty.
        target_size: Image dimensions (224, 224).
        seed: Random seed for reproducibility.
        smoke_test: If True, runs 1 epoch on limited batches to verify pipeline.
        max_batches: Explicit limit on batches per epoch.
        checkpoint_name: Filename for saving best model checkpoint.
        resume_path: Optional path to checkpoint to resume training from.

    Returns:
        Summary dictionary with training results.
    """
    set_seed(seed)
    root = find_project_root()
    base_proc = root / "datasets" / "aptos" / "processed"

    train_csv = Path(train_manifest).resolve() if train_manifest else (base_proc / "train_manifest.csv")
    val_csv = Path(val_manifest).resolve() if val_manifest else (base_proc / "val_manifest.csv")
    out_dir = Path(output_dir).resolve() if output_dir else (root / "ai_models" / "retina" / "weights")

    if not train_csv.is_file():
        raise FileNotFoundError(f"Training manifest not found: {train_csv}")
    if not val_csv.is_file():
        raise FileNotFoundError(f"Validation manifest not found: {val_csv}")

    # Determine safe checkpoint filename
    target_checkpoint_name = checkpoint_name
    if target_checkpoint_name is None:
        target_checkpoint_name = "retinaguard_v2.pt"

    # Enforce protection: never allow overwriting best_model.pt in project weights dir
    validate_checkpoint_safety(out_dir, target_checkpoint_name, is_resuming=(resume_path is not None))

    # 1. Load balanced class weights from summary or compute
    summary_file = base_proc / "dataset_summary.json"
    weights_list: List[float] = [0.405960, 1.972391, 0.734085, 3.803896, 2.471730]
    if summary_file.is_file():
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
            weights_dict = summary_data.get("balanced_class_weights", {})
            if weights_dict:
                weights_list = [float(weights_dict[str(c)]) for c in range(5)]

    # 2. Datasets & Loaders
    train_prep = RetinaImagePreprocessor(
        target_size=target_size,
        normalize=True,
        is_training=True,
        augment=True,
        random_seed=seed,
    )
    val_prep = RetinaImagePreprocessor(
        target_size=target_size,
        normalize=True,
        is_training=False,
        augment=False,
    )

    train_dataset = RetinaFundusDataset(train_csv, preprocessor=train_prep, project_root=root)
    val_dataset = RetinaFundusDataset(val_csv, preprocessor=val_prep, project_root=root)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # Single-process for Windows safety
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    # 3. Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_retina_model(
        num_classes=5,
        pretrained=True,
        dropout=0.3,
        freeze_backbone=True,
        device=device,
    )

    # Smoke test settings
    effective_epochs = 1 if smoke_test else epochs
    batch_limit = max_batches or (3 if smoke_test else None)
    freeze_epochs = 0 if smoke_test else 1

    trainer = RetinaTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        class_weights=weights_list,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        output_dir=out_dir,
        device=device,
        max_batches_per_epoch=batch_limit,
        resume_checkpoint=resume_path,
        freeze_backbone_epochs=freeze_epochs,
    )

    results = trainer.train(
        total_epochs=effective_epochs,
        freeze_backbone_epochs=freeze_epochs,
        best_checkpoint_filename=target_checkpoint_name,
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Train or Resume RetinaGuard Diabetic Retinopathy Classifier")
    parser.add_argument("--epochs", type=int, default=10, help="Total training epochs (default: 10)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--max-batches", type=int, default=None, help="Maximum batches per epoch")
    parser.add_argument("--smoke-test", action="store_true", help="Run 1 quick smoke-test epoch")
    parser.add_argument("--checkpoint-name", type=str, default="retinaguard_v2.pt", help="Filename for saved best checkpoint")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint (.pt) to safely resume training from")
    args = parser.parse_args()

    train_retinaguard(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_batches=args.max_batches,
        smoke_test=args.smoke_test,
        checkpoint_name=args.checkpoint_name,
        resume_path=args.resume,
    )
