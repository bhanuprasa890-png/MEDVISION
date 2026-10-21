"""Image preprocessing and normalization pipeline for retinal fundus imaging.

Provides robust, reproducible, and model-agnostic image transforms for RetinaGuard:
1. Universal image loading (filepath, bytes, PIL Image, NumPy array).
2. Color space standardization: conversion to 3-channel RGB across any input mode.
3. Optional circular Field-of-View (FOV) / black border auto-cropping.
4. High-quality resampling and bicubic resizing to configurable dimensions.
5. ImageNet standardization / normalization for pretrained vision backbones.
6. Deterministic evaluation transforms (guarantees validation images are never randomly augmented).
7. Invertible denormalization for downstream visual explainability (Grad-CAM).
"""

from __future__ import annotations

import io
import math
import random
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple, Union

import numpy as np
from PIL import Image, ImageOps


# Standard ImageNet statistics (widely used by EfficientNet, ConvNeXt, ResNet, ViT)
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)


class RetinaImagePreprocessor:
    """Configurable preprocessing pipeline for retinal fundus images.

    Ensures consistent dimensions and intensity distributions across training,
    validation, and inference phases.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (512, 512),
        mean: Sequence[float] = IMAGENET_MEAN,
        std: Sequence[float] = IMAGENET_STD,
        normalize: bool = True,
        channels_first: bool = True,
        crop_black_margins: bool = False,
        is_training: bool = False,
        augment: bool = False,
        horizontal_flip_prob: float = 0.5,
        vertical_flip_prob: float = 0.5,
        random_seed: int | None = None,
    ) -> None:
        """Initialize preprocessor with target specifications.

        Args:
            target_size: Tuple of (width, height) for resizing.
            mean: Per-channel normalization mean (R, G, B).
            std: Per-channel normalization standard deviation (R, G, B).
            normalize: Whether to apply zero-mean unit-variance scaling.
            channels_first: If True, returns array with shape (3, H, W);
                if False, returns (H, W, 3).
            crop_black_margins: If True, auto-crops extraneous black borders.
            is_training: Whether pipeline is operating in training mode.
            augment: Whether to apply data augmentations (only active when is_training=True).
            horizontal_flip_prob: Probability of random horizontal reflection.
            vertical_flip_prob: Probability of random vertical reflection.
            random_seed: Optional fixed random seed for reproducible augmentations.
        """
        self.target_size = target_size
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)
        self.normalize = normalize
        self.channels_first = channels_first
        self.crop_black_margins = crop_black_margins
        self.is_training = is_training
        # CRITICAL: Augmentations are strictly disabled during validation / inference
        self.augment = augment and is_training
        self.horizontal_flip_prob = horizontal_flip_prob
        self.vertical_flip_prob = vertical_flip_prob
        self._rng = random.Random(random_seed) if random_seed is not None else random.Random()

    @staticmethod
    def load_image(image_input: Union[str, Path, bytes, io.BytesIO, Image.Image, np.ndarray]) -> Image.Image:
        """Load an image from various input representations into a PIL Image.

        Args:
            image_input: Path, raw bytes, BytesIO stream, PIL Image, or NumPy array.

        Returns:
            Pillow Image object.

        Raises:
            ValueError: If input format is unsupported or bytes cannot be decoded.
        """
        if isinstance(image_input, Image.Image):
            return image_input.copy()

        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            if path.stat().st_size == 0:
                raise ValueError(f"Image file is empty (0 bytes): {path}")
            with Image.open(path) as img:
                return img.copy()

        if isinstance(image_input, (bytes, bytearray)):
            if len(image_input) == 0:
                raise ValueError("Image bytes input is empty (0 bytes).")
            with Image.open(io.BytesIO(image_input)) as img:
                return img.copy()

        if isinstance(image_input, io.BytesIO):
            image_input.seek(0)
            with Image.open(image_input) as img:
                return img.copy()

        if isinstance(image_input, np.ndarray):
            if image_input.dtype != np.uint8:
                # If float array in [0, 1], scale to uint8 [0, 255]
                if np.issubdtype(image_input.dtype, np.floating) and image_input.max() <= 1.0:
                    image_input = (image_input * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    image_input = image_input.clip(0, 255).astype(np.uint8)
            return Image.fromarray(image_input)

        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    @staticmethod
    def convert_to_rgb(img: Image.Image) -> Image.Image:
        """Convert any PIL image mode to standardized 3-channel RGB.

        Handles:
            - RGBA: Blends alpha over black background (retina photographs have dark perimeter).
            - L (grayscale): Duplicates single channel to 3 channels.
            - P (palette) & CMYK: Evaluates color palette to true RGB.

        Args:
            img: Pillow Image object.

        Returns:
            RGB Pillow Image.
        """
        if img.mode == "RGB":
            return img

        if img.mode == "RGBA":
            # Composite over black background
            background = Image.new("RGB", img.size, (0, 0, 0))
            background.paste(img, mask=img.split()[3])  # 3 is alpha channel
            return background

        if img.mode in ("LA", "PA"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (0, 0, 0))
            background.paste(img, mask=img.split()[3])
            return background

        return img.convert("RGB")

    @staticmethod
    def crop_fov_borders(img: Image.Image, tolerance: int = 10) -> Image.Image:
        """Crop uninformative black perimeter borders around the circular retina.

        Args:
            img: RGB Pillow Image.
            tolerance: Threshold below which pixels are considered black.

        Returns:
            Cropped RGB Pillow Image.
        """
        # Convert to grayscale for quick bounding box estimation
        gray = img.convert("L")
        # Mask where intensity exceeds tolerance
        mask = gray.point(lambda p: 255 if p > tolerance else 0)
        bbox = mask.getbbox()
        if bbox is not None:
            # Check aspect ratio to avoid extreme narrow sliver crops
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width > 16 and height > 16:
                return img.crop(bbox)
        return img

    def resize(self, img: Image.Image) -> Image.Image:
        """Resize image to target dimensions using bicubic interpolation.

        Args:
            img: RGB Pillow Image.

        Returns:
            Resized RGB Pillow Image.
        """
        if img.size == self.target_size:
            return img
        return img.resize(self.target_size, resample=Image.Resampling.BICUBIC)

    def apply_training_augmentations(self, img: Image.Image) -> Image.Image:
        """Apply deterministic or randomized augmentations for training data only.

        CRITICAL: Never invoked if is_training=False or augment=False.

        Args:
            img: RGB Pillow Image.

        Returns:
            Augmented Pillow Image.
        """
        if not self.augment or not self.is_training:
            return img

        # Random horizontal reflection
        if self._rng.random() < self.horizontal_flip_prob:
            img = ImageOps.mirror(img)

        # Random vertical reflection
        if self._rng.random() < self.vertical_flip_prob:
            img = ImageOps.flip(img)

        return img

    def normalize_array(self, img_array: np.ndarray) -> np.ndarray:
        """Scale array to [0.0, 1.0] and standardize with ImageNet mean and std.

        Args:
            img_array: Float or uint8 NumPy array of shape (H, W, 3).

        Returns:
            Normalized float32 NumPy array with shape (3, H, W) or (H, W, 3).
        """
        # Convert to float32 and scale to [0, 1] if in [0, 255]
        arr = img_array.astype(np.float32)
        if arr.max() > 1.0:
            arr /= 255.0

        if self.normalize:
            # Broadcast mean and std across spatial dimensions: (H, W, 3) - (3,)
            arr = (arr - self.mean) / self.std

        if self.channels_first:
            # (H, W, 3) -> (3, H, W)
            arr = np.transpose(arr, (2, 0, 1))

        return arr

    def denormalize_array(self, norm_array: np.ndarray) -> np.ndarray:
        """Invert normalization to recover original [0, 255] uint8 RGB representation.

        Args:
            norm_array: Normalized float32 NumPy array (3, H, W) or (H, W, 3).

        Returns:
            uint8 NumPy array with shape (H, W, 3) in range [0, 255].
        """
        arr = norm_array.copy()
        if arr.ndim == 3 and arr.shape[0] == 3 and self.channels_first:
            arr = np.transpose(arr, (1, 2, 0))

        if self.normalize:
            arr = (arr * self.std) + self.mean

        arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
        return arr

    def preprocess_pil(
        self,
        image_input: Union[str, Path, bytes, io.BytesIO, Image.Image, np.ndarray],
    ) -> Image.Image:
        """Execute image transforms up to resizing, returning a PIL Image.

        Args:
            image_input: Input image in any supported format.

        Returns:
            Preprocessed RGB Pillow Image of dimensions `target_size`.
        """
        img = self.load_image(image_input)
        img = self.convert_to_rgb(img)

        if self.crop_black_margins:
            img = self.crop_fov_borders(img)

        if self.is_training and self.augment:
            img = self.apply_training_augmentations(img)

        img = self.resize(img)
        return img

    def preprocess(
        self,
        image_input: Union[str, Path, bytes, io.BytesIO, Image.Image, np.ndarray],
    ) -> np.ndarray:
        """Full end-to-end preprocessing pipeline.

        Performs:
        1. Universal image loading.
        2. RGB conversion.
        3. Optional FOV border crop.
        4. Augmentation (if training mode active).
        5. Bicubic resizing.
        6. Intensity scaling and channel normalization.

        Args:
            image_input: Image filepath, raw bytes, PIL Image, or array.

        Returns:
            Preprocessed float32 NumPy array ready for deep neural network input.
        """
        pil_img = self.preprocess_pil(image_input)
        img_array = np.asarray(pil_img, dtype=np.float32)
        return self.normalize_array(img_array)


def preprocess_retina_image(
    image_bytes: bytes,
    target_size: Tuple[int, int] = (512, 512),
    normalize: bool = True,
    channels_first: bool = True,
) -> Dict[str, Any]:
    """Production preprocessing step for retinal fundus images.

    Converts binary image bytes to standardized, normalized tensor format.
    Maintains compatibility with MedVision AI RetinaGuard module contracts.

    Args:
        image_bytes: Raw binary image content.
        target_size: Desired (width, height) tuple for downstream neural network.
        normalize: Whether to apply ImageNet normalization.
        channels_first: Whether output shape is (3, H, W) or (H, W, 3).

    Returns:
        Dictionary containing preprocessed status, shape, range, and tensor.

    Raises:
        ValueError: If image bytes are empty or corrupted.
    """
    preprocessor = RetinaImagePreprocessor(
        target_size=target_size,
        normalize=normalize,
        channels_first=channels_first,
        is_training=False,  # Inference / API evaluation is never augmented
        augment=False,
    )

    tensor = preprocessor.preprocess(image_bytes)

    return {
        "status": "SUCCESS",
        "shape": list(tensor.shape),
        "target_size": target_size,
        "channels": 3,
        "mean": list(preprocessor.mean),
        "std": list(preprocessor.std),
        "min_value": float(tensor.min()),
        "max_value": float(tensor.max()),
        "tensor": tensor,
    }
