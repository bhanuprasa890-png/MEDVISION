"""Retinal fundus image classification neural network architecture.

Defines the core RetinaGuard classifier based on transfer learning with ResNet-18:
1. Pretrained ResNet-18 backbone (ImageNet-1K V1 weights).
2. Custom classification head adapted for 5-class Diabetic Retinopathy grading:
   - Class 0: No DR
   - Class 1: Mild NPDR
   - Class 2: Moderate NPDR
   - Class 3: Severe NPDR
   - Class 4: Proliferative DR
3. Modality-specific dropout regularization to counter overfitting on medical datasets.
4. Feature layer exposure (layer4) for downstream Grad-CAM explainability in Step 4.
5. Robust checkpoint serialization and deserialization.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import ResNet18_Weights

logger = logging.getLogger("medvision.retina.model")

DR_CLASS_NAMES: Dict[int, str] = {
    0: "No Diabetic Retinopathy",
    1: "Mild Non-Proliferative DR",
    2: "Moderate Non-Proliferative DR",
    3: "Severe Non-Proliferative DR",
    4: "Proliferative Diabetic Retinopathy",
}


class RetinaResNet18(nn.Module):
    """ResNet-18 architecture with transfer learning for retinal fundus classification."""

    def __init__(
        self,
        num_classes: int = 5,
        pretrained: bool = True,
        dropout: float = 0.3,
        freeze_backbone: bool = False,
    ) -> None:
        """Initialize the network.

        Args:
            num_classes: Number of target diagnosis classes (default 5 for APTOS).
            pretrained: Whether to load ImageNet-1K pretrained weights.
            dropout: Dropout probability before the classification head.
            freeze_backbone: If True, freeze all convolutional layers for initial feature extraction.
        """
        super().__init__()
        self.num_classes = num_classes
        self.pretrained = pretrained
        self.dropout_rate = dropout

        # 1. Base Backbone
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet18(weights=weights)

        in_features = self.backbone.fc.in_features  # 512 for ResNet-18

        # 2. Custom Classification Head
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features=in_features, out_features=num_classes),
        )

        if freeze_backbone:
            self.set_backbone_trainable(False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (batch_size, 3, height, width).

        Returns:
            Logits tensor of shape (batch_size, num_classes).
        """
        return self.backbone(x)

    def get_last_conv_layer(self) -> nn.Module:
        """Retrieve reference to the final convolutional block (layer4) for Grad-CAM."""
        return self.backbone.layer4

    def set_backbone_trainable(self, trainable: bool = True) -> None:
        """Freeze or unfreeze the convolutional feature extractor layers.

        Args:
            trainable: If False, disables gradient tracking on backbone conv layers.
        """
        for name, param in self.backbone.named_parameters():
            if "fc" not in name:
                param.requires_grad = trainable

    def count_parameters(self) -> Dict[str, int]:
        """Compute trainable and total parameter counts."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total_parameters": total, "trainable_parameters": trainable}

    def save_checkpoint(
        self,
        filepath: Union[Path, str],
        epoch: int = 0,
        val_macro_f1: float = 0.0,
        val_loss: float = 0.0,
        optimizer_state: Optional[Dict[str, Any]] = None,
        scheduler_state: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Save a comprehensive checkpoint to disk atomically.

        Args:
            filepath: Destination file path.
            epoch: Current training epoch index.
            val_macro_f1: Best or current validation macro F1 score.
            val_loss: Current validation loss.
            optimizer_state: Optional optimizer state dictionary.
            scheduler_state: Optional learning rate scheduler state dictionary.
            config: Optional training configuration dictionary.

        Returns:
            Path object of the saved checkpoint.
        """
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model_architecture": "RetinaResNet18",
            "num_classes": self.num_classes,
            "dropout": self.dropout_rate,
            "epoch": epoch,
            "val_macro_f1": val_macro_f1,
            "val_loss": val_loss,
            "state_dict": self.state_dict(),
            "optimizer_state": optimizer_state,
            "scheduler_state": scheduler_state,
            "config": config or {},
        }
        # Atomic write: serialize to process-specific temporary file, then atomic rename
        tmp_path = path.with_suffix(f"{path.suffix}.tmp_{os.getpid()}")
        torch.save(payload, tmp_path)
        os.replace(tmp_path, path)
        return path

    @classmethod
    def load_from_checkpoint(
        cls,
        filepath: Union[Path, str],
        map_location: Optional[Union[str, torch.device]] = None,
    ) -> Tuple["RetinaResNet18", Dict[str, Any]]:
        """Instantiate and load model weights from a checkpoint file.

        Args:
            filepath: Path to saved checkpoint (.pt file).
            map_location: PyTorch device mapping (e.g., 'cpu' or 'cuda').

        Returns:
            Tuple of (model_instance, checkpoint_metadata_dict).
        """
        path = Path(filepath).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Checkpoint not found at: {path}")

        map_loc = map_location or torch.device("cpu")
        checkpoint = torch.load(path, map_location=map_loc)

        num_classes = checkpoint.get("num_classes", 5)
        dropout = checkpoint.get("dropout", 0.3)

        model = cls(num_classes=num_classes, pretrained=False, dropout=dropout)
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()

        return model, checkpoint


def build_retina_model(
    num_classes: int = 5,
    pretrained: bool = True,
    dropout: float = 0.3,
    freeze_backbone: bool = False,
    checkpoint_path: Optional[Union[Path, str]] = None,
    device: Optional[torch.device] = None,
) -> RetinaResNet18:
    """Factory function to build or restore a RetinaGuard classification network.

    Args:
        num_classes: Number of diagnostic target classes (0-4).
        pretrained: Whether to initialize with ImageNet weights.
        dropout: Regularization dropout probability.
        freeze_backbone: Whether to freeze backbone weights initially.
        checkpoint_path: Optional path to a trained checkpoint.
        device: Target torch device.

    Returns:
        Configured RetinaResNet18 instance.
    """
    if checkpoint_path is not None:
        model, _ = RetinaResNet18.load_from_checkpoint(checkpoint_path, map_location=device)
    else:
        model = RetinaResNet18(
            num_classes=num_classes,
            pretrained=pretrained,
            dropout=dropout,
            freeze_backbone=freeze_backbone,
        )

    if device is not None:
        model = model.to(device)

    return model
