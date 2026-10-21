from typing import Any, Dict, Optional
from PIL import Image

from .gradcam import RetinaGradCAM, apply_jet_colormap


class RetinaExplainabilityEngine:
    """Computes attribution maps (Grad-CAM) for RetinaGuard models."""

    def __init__(self, model_pipeline: Any = None) -> None:
        self.model_pipeline = model_pipeline
        self._gradcam: Optional[RetinaGradCAM] = None
        if model_pipeline is not None:
            model = getattr(model_pipeline, "model", model_pipeline)
            if model is not None:
                self._gradcam = RetinaGradCAM(model)

    def generate_heatmap(self, input_image: Any, target_class: int | None = None) -> Dict[str, Any]:
        """Generate explainability attribution mask and visualization overlay.

        Args:
            input_image: PIL Image, file path, numpy array, or tensor.
            target_class: Target class index to explain (defaults to argmax).

        Returns:
            Dictionary containing heatmap metadata and overlay data URIs.
        """
        if self._gradcam is None:
            raise RuntimeError(
                "RetinaExplainabilityEngine requires a model to generate heatmaps. "
                "Supply an initialized RetinaResNet18 or RetinaInferencePipeline."
            )
        return self._gradcam.generate_visualizations(input_image, target_class=target_class)
