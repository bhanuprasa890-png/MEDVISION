"""Retinal fundus image analysis pipeline package for MedVision AI."""

from .preprocessing import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    RetinaImagePreprocessor,
    preprocess_retina_image,
)
from .dataset import (
    DatasetValidationError,
    DatasetValidationReport,
    RetinaFundusDataset,
    compute_class_weights,
    create_stratified_split,
    find_project_root,
    generate_dataset_summary,
    load_aptos_csv,
    match_records_to_images,
    run_retina_data_pipeline,
    save_manifests,
    validate_dataset,
)
from .model import (
    DR_CLASS_NAMES,
    RetinaResNet18,
    build_retina_model,
)
from .train import RetinaTrainer, train_retinaguard
from .evaluate import (
    check_data_leakage,
    compute_multiclass_metrics,
    evaluate_retina_model,
    format_confusion_matrix,
    generate_markdown_report,
    run_evaluation,
)
from .inference import RetinaInferencePipeline
from .gradcam import RetinaGradCAM, apply_jet_colormap
from .explainability import RetinaExplainabilityEngine

__all__ = [
    "IMAGENET_MEAN",
    "IMAGENET_STD",
    "RetinaImagePreprocessor",
    "preprocess_retina_image",
    "DatasetValidationError",
    "DatasetValidationReport",
    "RetinaFundusDataset",
    "find_project_root",
    "load_aptos_csv",
    "match_records_to_images",
    "validate_dataset",
    "create_stratified_split",
    "compute_class_weights",
    "save_manifests",
    "generate_dataset_summary",
    "run_retina_data_pipeline",
    "DR_CLASS_NAMES",
    "RetinaResNet18",
    "build_retina_model",
    "RetinaTrainer",
    "train_retinaguard",
    "compute_multiclass_metrics",
    "evaluate_retina_model",
    "format_confusion_matrix",
    "generate_markdown_report",
    "check_data_leakage",
    "run_evaluation",
    "RetinaInferencePipeline",
    "RetinaGradCAM",
    "apply_jet_colormap",
    "RetinaExplainabilityEngine",
]


