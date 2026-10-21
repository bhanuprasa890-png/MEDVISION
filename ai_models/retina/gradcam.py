"""Grad-CAM (Gradient-weighted Class Activation Mapping) for RetinaGuard.

Provides visual explanations for RetinaResNet18 predictions by:
1. Capturing feature activations from the final convolutional layer (layer4).
2. Computing gradients of the predicted class score with respect to feature maps.
3. Performing global average pooling on gradients to produce channel importance weights.
4. Computing the weighted combination followed by ReLU to isolate features with positive influence.
5. Bilinear upsampling to the input image dimensions and min-max normalization to [0.0, 1.0].
6. Generating Jet-colormap heatmaps and blended overlays as base64 data URIs.

CLINICAL DISCLAIMER:
Grad-CAM heatmaps highlight image regions that strongly influenced the model's internal
features. They do NOT provide definitive proof or confirmation of retinal pathology,
microaneurysms, or hemorrhages. All outputs are strictly for research exploration.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from .model import DR_CLASS_NAMES, RetinaResNet18
from .preprocessing import RetinaImagePreprocessor

logger = logging.getLogger("medvision.retina.gradcam")


def apply_jet_colormap(heatmap: np.ndarray) -> np.ndarray:
    """Map a normalized 2D heatmap in [0.0, 1.0] to a 3-channel RGB Jet colormap.

    Pure NumPy implementation with zero external dependencies (no OpenCV/matplotlib).

    Args:
        heatmap: 2D NumPy array of shape (H, W) with float values in [0.0, 1.0].

    Returns:
        3D NumPy array of shape (H, W, 3) with uint8 RGB values in [0, 255].
    """
    x = np.clip(heatmap, 0.0, 1.0)
    # Piecewise linear approximation of the Jet colormap
    r = np.clip(1.5 - np.abs(4.0 * x - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(4.0 * x - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(4.0 * x - 1.0), 0.0, 1.0)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255.0).astype(np.uint8)


class RetinaGradCAM:
    """Computes Grad-CAM attribution heatmaps for RetinaResNet18 models."""

    def __init__(
        self,
        model: nn.Module,
        target_layer: Optional[nn.Module] = None,
        target_size: Tuple[int, int] = (224, 224),
    ) -> None:
        """Initialize Grad-CAM explainer.

        Args:
            model: PyTorch neural network (typically RetinaResNet18).
            target_layer: Convolutional layer to hook. If None, resolves model.get_last_conv_layer().
            target_size: Image resolution for upsampling the heatmap (default 224x224).

        Raises:
            ValueError: If target_layer is None and cannot be automatically detected.
        """
        self.model = model
        self.model.eval()
        self.target_size = target_size

        if target_layer is not None:
            self.target_layer = target_layer
        elif hasattr(model, "get_last_conv_layer"):
            self.target_layer = model.get_last_conv_layer()
        elif hasattr(model, "backbone") and hasattr(model.backbone, "layer4"):
            self.target_layer = model.backbone.layer4
        else:
            raise ValueError(
                "Cannot resolve target convolutional layer for Grad-CAM. "
                "Ensure model provides get_last_conv_layer() or specify target_layer explicitly."
            )

        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None

    def _fwd_hook(self, module: nn.Module, input: Any, output: torch.Tensor) -> None:
        self._activations = output

    def _bwd_hook(self, module: nn.Module, grad_input: Any, grad_output: Tuple[torch.Tensor, ...]) -> None:
        self._gradients = grad_output[0]

    def compute_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, int, float]:
        """Generate normalized 2D Grad-CAM heatmap for a given input tensor.

        Args:
            input_tensor: 4D Tensor of shape (1, 3, H, W).
            target_class: Class index (0-4) to compute attribution for. If None, uses argmax prediction.

        Returns:
            Tuple of:
            - cam: 2D numpy array of shape (H, W) normalized to [0.0, 1.0].
            - target_class: Class index for which CAM was computed.
            - class_score: Raw logit score of the target class.

        Raises:
            ValueError: If input tensor does not have 4 dimensions or batch size > 1.
            RuntimeError: If gradients could not be calculated or layer produces empty maps.
        """
        if input_tensor.ndim != 4 or input_tensor.size(0) != 1:
            raise ValueError(f"Grad-CAM requires input tensor with shape (1, 3, H, W), got {input_tensor.shape}")

        device = next(self.model.parameters()).device
        tensor = input_tensor.to(device)

        # Clear prior hooks & buffers
        self._activations = None
        self._gradients = None

        h_fwd = self.target_layer.register_forward_hook(self._fwd_hook)
        h_bwd = self.target_layer.register_full_backward_hook(self._bwd_hook)

        try:
            self.model.zero_grad()
            logits = self.model(tensor)

            if target_class is None:
                target_class = int(logits.argmax(dim=-1).item())

            if not (0 <= target_class < logits.size(-1)):
                raise ValueError(f"target_class {target_class} out of bounds (0-{logits.size(-1) - 1})")

            score = logits[0, target_class]
            score.backward(retain_graph=False)

        finally:
            h_fwd.remove()
            h_bwd.remove()

        if self._activations is None or self._gradients is None:
            raise RuntimeError("Grad-CAM hooks failed to capture activations or gradients.")

        # 1. Global Average Pooling over spatial dimensions of gradients
        # grads shape: (1, Channels, H_feat, W_feat) -> weights shape: (1, Channels, 1, 1)
        weights = torch.mean(self._gradients, dim=(2, 3), keepdim=True)

        # 2. Weighted linear sum of feature activations
        # acts shape: (1, Channels, H_feat, W_feat)
        cam = torch.sum(weights * self._activations, dim=1, keepdim=True)

        # 3. Apply ReLU: only positive influences on the target class are retained
        cam = torch.relu(cam)

        # 4. Upsample to target size via bilinear interpolation
        target_h, target_w = self.target_size
        cam = torch.nn.functional.interpolate(
            cam,
            size=(target_h, target_w),
            mode="bilinear",
            align_corners=False,
        )

        cam_tensor = cam.squeeze().detach().cpu()
        cam_min = float(cam_tensor.min().item())
        cam_max = float(cam_tensor.max().item())

        # 5. Min-Max normalization to [0.0, 1.0]
        if (cam_max - cam_min) > 1e-8:
            cam_norm = (cam_tensor - cam_min) / (cam_max - cam_min)
        else:
            cam_norm = torch.zeros_like(cam_tensor)

        cam_np = cam_norm.numpy().astype(np.float32)
        return cam_np, target_class, float(score.item())

    def generate_visualizations(
        self,
        original_image: Union[Image.Image, np.ndarray, str],
        preprocessor: Optional[RetinaImagePreprocessor] = None,
        target_class: Optional[int] = None,
        overlay_alpha: float = 0.4,
    ) -> Dict[str, Any]:
        """Generate high-level Grad-CAM visualizations and base64 data URIs.

        Args:
            original_image: PIL Image, RGB numpy array, or image file path.
            preprocessor: Image preprocessor instance (default: RetinaImagePreprocessor 224x224).
            target_class: Class index for explanation (None for model's argmax).
            overlay_alpha: Blend opacity for the heatmap over the fundus photo (0.0 to 1.0).

        Returns:
            Dictionary containing:
            - target_class: integer class explained.
            - target_class_label: human-readable DR severity.
            - heatmap_overlay_base64: data URI string (data:image/png;base64,...).
            - raw_heatmap_base64: data URI string for the standalone color heatmap.
            - salient_region_summary: coordinate and intensity summary of peak attention.
            - interpretability_disclaimer: clinical context notice.
        """
        # 1. Resolve PIL Image
        if isinstance(original_image, (str, bytes)):
            if isinstance(original_image, bytes):
                pil_img = Image.open(io.BytesIO(original_image)).convert("RGB")
            else:
                pil_img = Image.open(original_image).convert("RGB")
        elif isinstance(original_image, np.ndarray):
            pil_img = Image.fromarray(original_image).convert("RGB")
        elif isinstance(original_image, Image.Image):
            pil_img = original_image.convert("RGB")
        else:
            raise TypeError(f"Unsupported image type: {type(original_image)}")

        # 2. Preprocess to model tensor
        prep = preprocessor or RetinaImagePreprocessor(
            target_size=self.target_size,
            normalize=True,
            is_training=False,
            augment=False,
        )
        tensor_np = prep.preprocess(pil_img)
        input_tensor = torch.from_numpy(tensor_np).unsqueeze(0).float()

        # 3. Compute 2D CAM array
        cam_2d, resolved_class, logit_score = self.compute_cam(
            input_tensor,
            target_class=target_class,
        )

        # 4. Colorize heatmap via Jet palette
        heatmap_rgb = apply_jet_colormap(cam_2d)
        heatmap_img = Image.fromarray(heatmap_rgb)

        # 5. Blend with resized original image
        resized_orig = pil_img.resize(self.target_size, Image.Resampling.BICUBIC)
        orig_np = np.array(resized_orig, dtype=np.float32)
        heat_np = heatmap_rgb.astype(np.float32)

        alpha = float(np.clip(overlay_alpha, 0.0, 1.0))
        overlay_np = np.clip((1.0 - alpha) * orig_np + alpha * heat_np, 0, 255).astype(np.uint8)
        overlay_img = Image.fromarray(overlay_np)

        # 6. Encode to base64 data URIs
        overlay_buffer = io.BytesIO()
        overlay_img.save(overlay_buffer, format="PNG")
        overlay_base64 = f"data:image/png;base64,{base64.b64encode(overlay_buffer.getvalue()).decode('utf-8')}"

        heatmap_buffer = io.BytesIO()
        heatmap_img.save(heatmap_buffer, format="PNG")
        heatmap_base64 = f"data:image/png;base64,{base64.b64encode(heatmap_buffer.getvalue()).decode('utf-8')}"

        # 7. Compute salient region metadata (peak coordinates)
        peak_idx = np.unravel_index(np.argmax(cam_2d), cam_2d.shape)
        mean_intensity = float(np.mean(cam_2d))
        peak_intensity = float(np.max(cam_2d))

        return {
            "target_class": resolved_class,
            "target_class_label": DR_CLASS_NAMES.get(resolved_class, f"Class {resolved_class}"),
            "logit_score": round(logit_score, 4),
            "target_layer": "layer4 (BasicBlock conv2)",
            "resolution": list(self.target_size),
            "heatmap_overlay_base64": overlay_base64,
            "raw_heatmap_base64": heatmap_base64,
            "salient_region_summary": {
                "peak_y": int(peak_idx[0]),
                "peak_x": int(peak_idx[1]),
                "peak_intensity": round(peak_intensity, 4),
                "mean_intensity": round(mean_intensity, 4),
                "active_area_ratio": round(float(np.mean(cam_2d > 0.5)), 4),
            },
            "interpretability_note": (
                "Grad-CAM visualizes regions of the retinal fundus image that contributed most "
                "strongly to the neural network's feature activation for this diagnosis. "
                "Highlighted areas indicate model attention, NOT verified medical pathology."
            ),
        }
