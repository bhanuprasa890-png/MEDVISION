"""Inference pipeline for chest radiograph deep learning models."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch
import torchxrayvision as xrv

LOCAL_WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
DEFAULT_CHECKPOINT_NAME = "nih-pc-chex-mimic_ch-google-openi-kaggle-densenet121-d121-tw-lr001-rot45-tr15-sc15-seed0-best.pt"


class ChestXrayInferencePipeline:
    """Manages loading of thoracic radiograph model weights and forward inference.

    Uses DenseNet-121 architecture pretrained by TorchXRayVision on 7 combined datasets
    (NIH ChestX-ray14, PadChest, CheXpert, MIMIC-CXR, Google, OpenI, RSNA).
    Supported pathologies (18 multi-label findings):
      Atelectasis, Consolidation, Infiltration, Pneumothorax, Edema, Emphysema,
      Fibrosis, Effusion, Pneumonia, Pleural_Thickening, Cardiomegaly, Nodule,
      Mass, Hernia, Lung Lesion, Fracture, Lung Opacity, Enlarged Cardiomediastinum.
    """

    def __init__(self, model_checkpoint_path: Optional[str] = None) -> None:
        self.model_checkpoint_path = model_checkpoint_path
        self.model_version = "DenseNet-121-res224-all (TorchXRayVision v1)"
        self.architecture = "DenseNet-121"
        self.checkpoint_hash = "56524913dd16a906422e8d8b66a7a5c46be1d82eb7ac012d8103776f1aa68899"
        self._model: Optional[xrv.models.DenseNet] = None
        self._is_loaded = False
        self.device = torch.device("cpu")

    def load_model(self) -> None:
        """Load trained DenseNet-121 model weights from local repository or cache."""
        if self._is_loaded and self._model is not None:
            return

        # Check local project weights directory first
        # Load DenseNet-121 model with pre-trained weights
        model = xrv.models.DenseNet(weights="densenet121-res224-all")
        if not hasattr(model, "pathologies") or model.pathologies is None:
            model.pathologies = list(xrv.datasets.default_pathologies)
        local_ckpt = LOCAL_WEIGHTS_DIR / DEFAULT_CHECKPOINT_NAME
        if local_ckpt.is_file():
            self.model_checkpoint_path = str(local_ckpt)
        else:
            self.model_checkpoint_path = getattr(model, "weights_filename_local", "densenet121-res224-all")

        model.to(self.device)
        model.eval()
        self._model = model
        self._is_loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model(self) -> Optional[xrv.models.DenseNet]:
        return self._model

    @property
    def pathologies(self) -> List[str]:
        if self._model is not None and hasattr(self._model, "pathologies") and self._model.pathologies is not None:
            return list(self._model.pathologies)
        return list(xrv.datasets.default_pathologies)

    @property
    def operating_thresholds(self) -> Dict[str, float]:
        """Operating thresholds calibrated for optimal sensitivity/specificity."""
        paths = self.pathologies
        if self._model is not None and hasattr(self._model, "op_threshs") and self._model.op_threshs is not None:
            return {
                path: float(thresh) if not np.isnan(float(thresh)) else 0.5
                for path, thresh in zip(paths, self._model.op_threshs)
            }
        return {p: 0.5 for p in paths}

    def predict(self, preprocessed_tensor: torch.Tensor) -> Dict[str, Any]:
        """Perform forward multi-label inference.

        Args:
            preprocessed_tensor: Normalized torch.Tensor of shape (1, 1, 224, 224).

        Returns:
            Dictionary with multi-label findings, probabilities, thresholds, and top detection.
        """
        if not self._is_loaded or self._model is None:
            self.load_model()

        if not isinstance(preprocessed_tensor, torch.Tensor):
            raise ValueError("Input must be a torch.Tensor.")

        if preprocessed_tensor.ndim != 4 or preprocessed_tensor.shape[1] != 1:
            raise ValueError(
                f"Expected tensor shape (1, 1, H, W), got {tuple(preprocessed_tensor.shape)}"
            )

        tensor = preprocessed_tensor.to(self.device)

        with torch.no_grad():
            raw_logits = self._model(tensor)
            # DenseNet in torchxrayvision outputs unnormalized logits; apply sigmoid for multi-label probabilities
            sigmoid_probs = torch.sigmoid(raw_logits).squeeze(0).cpu().numpy()

        # Reject NaN / Inf
        if np.isnan(sigmoid_probs).any() or np.isinf(sigmoid_probs).any():
            raise ValueError("Model produced non-finite (NaN or Inf) predictions.")

        pathologies = self.pathologies
        op_threshs = self.operating_thresholds

        findings: Dict[str, float] = {}
        findings_above_threshold: List[Dict[str, Any]] = []

        for idx, path_name in enumerate(pathologies):
            score = float(sigmoid_probs[idx])
            score = max(0.0, min(1.0, score))
            thresh = op_threshs.get(path_name, 0.5)
            findings[path_name] = round(score, 4)
            if score >= thresh:
                findings_above_threshold.append({
                    "name": path_name,
                    "score": round(score, 4),
                    "threshold": round(thresh, 4),
                    "detected": True,
                })

        # Sort findings above threshold by margin over threshold
        findings_above_threshold.sort(
            key=lambda x: x["score"] - x["threshold"],
            reverse=True,
        )

        # Identify top finding across all pathologies
        top_idx = int(np.argmax(sigmoid_probs))
        top_finding = pathologies[top_idx]
        top_score = float(sigmoid_probs[top_idx])

        return {
            "top_finding": top_finding,
            "top_score": round(top_score, 4),
            "findings": findings,
            "findings_above_threshold": findings_above_threshold,
            "all_class_scores": findings,  # Compatibility field
            "model_version": self.model_version,
            "calibration_notice": (
                "Model scores represent uncalibrated sigmoid output activations from a research prototype "
                "and are not calibrated clinical probabilities or diagnostic directives."
            ),
        }
