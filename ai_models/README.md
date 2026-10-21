# AI/ML Engine — MedVision AI

## 1. Overview & Ethical AI Guidelines

This directory houses the machine learning and explainability (XAI) pipelines for MedVision AI.

### Core Ethical Guidelines:
- **No Pseudo-AI**: Never fabricate clinical predictions, confidence scores, or diagnostic reports when a model is not yet trained or loaded.
- **Explainability First**: Every future medical inference pipeline must pair any classification prediction with an explainability artifact (e.g., Grad-CAM, Integrated Gradients) highlighting the region of interest.
- **Model Checkpoints**: Real weights (`*.pt`, `*.onnx`, `*.h5`) are large binary files and are strictly excluded via `.gitignore`. Weights should be loaded via configuration paths or cloud object stores.

---

## 2. Directory Structure

```text
ai_models/
├── retina/                 # Retinal fundus pipeline
│   ├── preprocessing.py    # Image normalization, cropping, and Ben Graham transforms
│   ├── inference.py        # Model loading & inference abstraction (placeholder)
│   ├── explainability.py   # Grad-CAM / saliency map generators (placeholder)
│   └── README.md           # Retinal model specs, datasets & preprocessing details
├── chest_xray/             # Chest X-Ray (CXR) radiograph pipeline
│   ├── preprocessing.py    # Grayscale conversion, CLAHE, resizing
│   ├── inference.py        # Model loading & inference abstraction (placeholder)
│   ├── explainability.py   # Grad-CAM / attention map generators (placeholder)
│   └── README.md           # CXR model specs, datasets & preprocessing details
└── README.md               # Directory overview and roadmap
```

---

## 3. Pipeline Lifecycle

Each modality follows a three-stage lifecycle:
1. **`preprocessing.py`**: Validates input array dimensions, rescales pixel intensities, and applies modality-specific color/contrast adjustments.
2. **`inference.py`**: Instantiates the neural architecture, loads weights, performs forward pass in evaluation mode (`torch.no_grad()`), and extracts logits.
3. **`explainability.py`**: Computes gradient activations at target convolutional layers to produce visual attribution heatmaps overlaid on the original scan.
