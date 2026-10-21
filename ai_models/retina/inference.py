"""Inference pipeline for retinal fundus models."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import torch

from PIL import Image

from .model import DR_CLASS_NAMES, RetinaResNet18
from .preprocessing import RetinaImagePreprocessor


class RetinaInferencePipeline:
    """Manages loading of neural network weights and forward-pass inference.

    Architecture: ResNet-18 with 5-class Diabetic Retinopathy classification head.
    Classes:
        0: No Diabetic Retinopathy
        1: Mild Non-Proliferative DR
        2: Moderate Non-Proliferative DR
        3: Severe Non-Proliferative DR
        4: Proliferative Diabetic Retinopathy
    """

    def __init__(
        self,
        model_checkpoint_path: Optional[Union[str, Path]] = None,
        target_size: tuple[int, int] = (224, 224),
    ) -> None:
        self.model_checkpoint_path = Path(model_checkpoint_path) if model_checkpoint_path else None
        self.model_version = "retina_resnet18_v1.0"
        self._is_loaded = False
        self.model: Optional[RetinaResNet18] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.target_size = target_size
        self.preprocessor = RetinaImagePreprocessor(
            target_size=target_size,
            normalize=True,
            is_training=False,
            augment=False,
        )

        if self.model_checkpoint_path and self.model_checkpoint_path.is_file():
            self.load_model(self.model_checkpoint_path)

    def load_model(self, checkpoint_path: Optional[Union[str, Path]] = None) -> None:
        """Load trained model weights from disk.

        Args:
            checkpoint_path: Optional path override to checkpoint file (.pt).

        Raises:
            FileNotFoundError: If checkpoint file does not exist.
        """
        path = Path(checkpoint_path or self.model_checkpoint_path or "").resolve()
        if not path.is_file():
            raise FileNotFoundError(
                f"Retina model checkpoint not found at: {path}. "
                "Train the model first or supply a valid checkpoint path."
            )

        self.model, metadata = RetinaResNet18.load_from_checkpoint(path, map_location=self.device)
        self.model.to(self.device)
        self.model.eval()
        self.model_checkpoint_path = path
        self._is_loaded = True
        self.model_version = metadata.get("config", {}).get("model_version", "retina_resnet18_v1.0")

    def predict(
        self,
        input_data: Union[torch.Tensor, np.ndarray, Image.Image, str, Path],
    ) -> Dict[str, Any]:
        """Perform forward inference on an image or preprocessed tensor.

        Args:
            input_data: PIL Image, file path, normalized torch.Tensor, or numpy array.

        Returns:
            Dictionary with predicted class, class name, confidence, probabilities, and model version.

        Raises:
            RuntimeError: If model is not loaded prior to inference.
        """
        if not self._is_loaded or self.model is None:
            raise RuntimeError(
                "RetinaInferencePipeline is not loaded. Call load_model(checkpoint_path) before predict()."
            )

        # 1. Handle PIL Image or file path
        if isinstance(input_data, (str, Path)):
            img = Image.open(input_data)
            tensor_np = self.preprocessor.preprocess(img)
            tensor = torch.from_numpy(tensor_np).float()
        elif isinstance(input_data, Image.Image):
            tensor_np = self.preprocessor.preprocess(input_data)
            tensor = torch.from_numpy(tensor_np).float()
        elif isinstance(input_data, np.ndarray):
            tensor = torch.from_numpy(input_data).float()
        elif isinstance(input_data, torch.Tensor):
            tensor = input_data.float()
        else:
            raise TypeError(f"Unsupported input type for inference: {type(input_data)}")

        # Add batch dimension if single image: (3, H, W) -> (1, 3, H, W)
        if tensor.ndim == 3:
            tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx])

        return {
            "predicted_class": pred_idx,
            "class_name": DR_CLASS_NAMES.get(pred_idx, f"Class {pred_idx}"),
            "confidence": round(confidence, 4),
            "probabilities": {str(c): round(float(p), 4) for c, p in enumerate(probs)},
            "model_version": self.model_version,
            "disclaimer": "RESEARCH PROTOTYPE ONLY: Not for clinical or diagnostic use.",
        }

