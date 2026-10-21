"""Explainability (XAI) engine for chest radiograph models.

Computes Grad-CAM (Gradient-weighted Class Activation Mapping) on the final
dense block of the DenseNet-121 backbone, providing visual attention heatmaps
highlighting thoracic regions influencing specific pathology predictions.
"""

import base64
import io
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F


def _colorize_cam_jet(cam: np.ndarray) -> np.ndarray:
    """Colorize a 2D float array in [0.0, 1.0] using a standard Jet colormap (RGB uint8)."""
    cam_clamped = np.clip(cam, 0.0, 1.0)
    # Simple, standalone vectorised Jet implementation without heavy matplotlib dependencies
    r = np.clip(1.5 - np.abs(cam_clamped * 4.0 - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(cam_clamped * 4.0 - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(cam_clamped * 4.0 - 1.0), 0.0, 1.0)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255.0).astype(np.uint8)


def _blend_heatmap_with_grayscale(
    grayscale_uint8: np.ndarray,
    colorized_cam_uint8: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    """Blend colorized Jet CAM onto a 2D grayscale radiograph."""
    if grayscale_uint8.ndim == 2:
        base_rgb = np.stack([grayscale_uint8] * 3, axis=-1).astype(np.float32)
    else:
        base_rgb = grayscale_uint8[:, :, :3].astype(np.float32)

    cam_rgb = colorized_cam_uint8.astype(np.float32)
    blended = (1.0 - alpha) * base_rgb + alpha * cam_rgb
    return np.clip(blended, 0.0, 255.0).astype(np.uint8)


def _array_to_png_base64(arr_uint8: np.ndarray) -> str:
    """Encode an RGB/RGBA numpy array as a base64 PNG data URI."""
    pil_img = Image.fromarray(arr_uint8)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    raw_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{raw_b64}"


class ChestXrayExplainabilityEngine:
    """Computes Grad-CAM attribution heatmaps for DenseNet-121 chest x-ray models."""

    def __init__(self, inference_pipeline: Any) -> None:
        self.pipeline = inference_pipeline
        self.target_layer_name = "denseblock4"

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        display_image: np.ndarray,
        target_pathology: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate explainability attribution mask and visualization overlay.

        Args:
            input_tensor: Preprocessed image tensor with shape (1, 1, 224, 224).
            display_image: 2D uint8 radiograph image of shape (224, 224) for blending.
            target_pathology: Name of pathology to explain. If None, uses top finding.

        Returns:
            Dictionary containing heatmap metadata, base64 overlays, and salient metrics.
        """
        model = self.pipeline.model
        if model is None:
            self.pipeline.load_model()
            model = self.pipeline.model

        pathologies = self.pipeline.pathologies
        if target_pathology is None or target_pathology not in pathologies:
            # Run forward pass first to find top pathology if not specified
            with torch.no_grad():
                logits = model(input_tensor)
                top_idx = int(torch.argmax(logits, dim=1).item())
                target_pathology = pathologies[top_idx]
                target_idx = top_idx
        else:
            target_idx = pathologies.index(target_pathology)

        # Enable gradient tracking on cloned input
        x = input_tensor.clone().detach().requires_grad_(True)

        activations = None
        gradients = None

        def forward_hook(m, inp, outp):
            nonlocal activations
            activations = outp

        def backward_hook(m, grad_in, grad_out):
            nonlocal gradients
            gradients = grad_out[0]

        target_layer = model.features.denseblock4
        h_forward = target_layer.register_forward_hook(forward_hook)
        h_backward = target_layer.register_full_backward_hook(backward_hook)

        try:
            model.zero_grad()
            logits = model(x)
            score = logits[0, target_idx]
            score.backward()
        finally:
            h_forward.remove()
            h_backward.remove()

        if activations is None or gradients is None:
            raise RuntimeError("Failed to capture feature activations or gradients for Grad-CAM.")

        # Channel-wise global average pooling of gradients
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        # Weighted combination of forward activation maps
        cam = (weights * activations).sum(dim=1, keepdim=True)
        # Apply ReLU to retain only features with positive influence on target
        cam = F.relu(cam)

        # Upsample CAM to display image resolution (224x224)
        cam_resized = F.interpolate(
            cam,
            size=(display_image.shape[0], display_image.shape[1]),
            mode="bilinear",
            align_corners=False,
        )
        cam_np = cam_resized.squeeze().detach().cpu().numpy()

        # Min-max normalization of CAM in [0.0, 1.0]
        cam_min, cam_max = float(cam_np.min()), float(cam_np.max())
        if cam_max > cam_min:
            cam_norm = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_norm = np.zeros_like(cam_np)

        # Metrics for salient region
        peak_idx = np.unravel_index(np.argmax(cam_norm), cam_norm.shape)
        peak_y, peak_x = int(peak_idx[0]), int(peak_idx[1])
        peak_intensity = float(cam_norm[peak_y, peak_x])
        mean_intensity = float(np.mean(cam_norm))
        active_area_ratio = float(np.mean(cam_norm > 0.5))

        # Colorize and blend
        colorized_cam = _colorize_cam_jet(cam_norm)
        blended_overlay = _blend_heatmap_with_grayscale(display_image, colorized_cam, alpha=0.45)

        raw_heatmap_base64 = _array_to_png_base64(colorized_cam)
        heatmap_overlay_base64 = _array_to_png_base64(blended_overlay)

        return {
            "target_pathology": target_pathology,
            "target_pathology_index": target_idx,
            "logit_score": float(score.detach().cpu().item()),
            "target_layer": self.target_layer_name,
            "resolution": [display_image.shape[0], display_image.shape[1]],
            "heatmap_overlay_base64": heatmap_overlay_base64,
            "raw_heatmap_base64": raw_heatmap_base64,
            "salient_region_summary": {
                "peak_y": peak_y,
                "peak_x": peak_x,
                "peak_intensity": round(peak_intensity, 4),
                "mean_intensity": round(mean_intensity, 4),
                "active_area_ratio": round(active_area_ratio, 4),
            },
            "interpretability_note": (
                "Grad-CAM visual attribution highlights thoracic regions that influenced the model's "
                f"prediction for '{target_pathology}'. Heatmaps reflect machine attention and do NOT "
                "confirm or rule out the clinical presence of lesions or disease."
            ),
        }
