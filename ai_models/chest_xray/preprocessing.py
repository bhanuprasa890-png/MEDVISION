"""Preprocessing module for chest radiography (CXR).

Standardizes raw radiograph image bytes into the exact tensor format
expected by the TorchXRayVision DenseNet-121 backbone:
1. Decode image bytes (JPEG, PNG, WebP), supporting RGBA transparency.
2. Convert to single-channel 2D grayscale float32 array in [0, 255].
3. Center-crop long dimension to preserve anatomical aspect ratio.
4. Resize to target resolution (224x224).
5. Normalize intensity range to [-1024, 1024] via xrv.utils.normalize.
6. Return torch.FloatTensor of shape (1, 1, 224, 224).
"""

import io
from typing import Any, Dict, Tuple
import numpy as np
from PIL import Image
import skimage.transform
import torch
import torchxrayvision as xrv


def decode_radiograph_to_grayscale(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes to a 2D float32 grayscale numpy array in range [0, 255]."""
    if not image_bytes:
        raise ValueError("Image content is empty.")
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.verify()
        # Re-open after verify as per PIL documentation
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError(f"Failed to decode radiograph: {exc}") from exc

    # Handle transparency by compositing onto black background
    if pil_img.mode in ("RGBA", "LA") or ("transparency" in pil_img.info):
        alpha_img = pil_img.convert("RGBA")
        background = Image.new("RGBA", alpha_img.size, (0, 0, 0, 255))
        composite = Image.alpha_composite(background, alpha_img)
        gray_img = composite.convert("L")
    else:
        gray_img = pil_img.convert("L")

    arr = np.array(gray_img, dtype=np.float32)
    return arr


def center_crop_radiograph(img: np.ndarray) -> np.ndarray:
    """Perform center crop on the longer dimension to preserve native aspect ratio."""
    h, w = img.shape[:2]
    crop_size = min(h, w)
    start_y = (h - crop_size) // 2
    start_x = (w - crop_size) // 2
    return img[start_y : start_y + crop_size, start_x : start_x + crop_size]


def resize_radiograph(img: np.ndarray, target_size: int = 224) -> np.ndarray:
    """Resize 2D radiograph array to (target_size, target_size) using skimage."""
    resized = skimage.transform.resize(
        img,
        (target_size, target_size),
        mode="constant",
        preserve_range=True,
    ).astype(np.float32)
    return resized


def preprocess_chest_xray_image(
    image_bytes: bytes,
    target_size: int = 224,
) -> Tuple[torch.Tensor, np.ndarray, Dict[str, Any]]:
    """Complete preprocessing pipeline for CXR radiograph.

    Args:
        image_bytes: Raw binary image content.
        target_size: Target square dimension (default 224 for DenseNet-121).

    Returns:
        Tuple containing:
        - tensor: Normalized torch.FloatTensor with shape (1, 1, target_size, target_size).
        - display_img: 2D float32 array in [0, 255] suitable for heatmap overlay blending.
        - metadata: Dictionary containing original dimensions and preprocessing stats.
    """
    raw_arr = decode_radiograph_to_grayscale(image_bytes)
    orig_h, orig_w = raw_arr.shape[:2]

    # Center crop to preserve aspect ratio
    cropped = center_crop_radiograph(raw_arr)

    # Resize to target resolution
    resized = resize_radiograph(cropped, target_size=target_size)

    # Ensure maxval is bounded to 255
    maxval = float(max(255.0, resized.max()))
    # Intensity normalization into [-1024, 1024]
    normalized = xrv.utils.normalize(resized, maxval=maxval)

    # Reshape to (1, 1, H, W)
    tensor = torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0).float()

    metadata = {
        "original_width": orig_w,
        "original_height": orig_h,
        "cropped_size": cropped.shape[0],
        "target_size": target_size,
        "normalized_min": float(normalized.min()),
        "normalized_max": float(normalized.max()),
    }

    # display_img in [0, 255]
    display_img = np.clip(resized, 0, 255).astype(np.uint8)

    return tensor, display_img, metadata
