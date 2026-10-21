"""In-memory file validation service for medical images.

Enforces:
1. File extension validation.
2. MIME type constraints.
3. Upload size limit (max 10MB).
4. Image integrity and dimension parsing via Pillow.
5. In-memory SHA-256 digest computation (zero disk persistence).
"""

import io
import os
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.security import calculate_sha256, sanitize_filename
from app.schemas.common import ImageMetadataSchema

# Defensive boundaries to prevent decompression bombs and pixel-flood memory exhaustion
MAX_IMAGE_DIMENSION: int = 10000
MAX_IMAGE_PIXELS: int = 25_000_000

# Set Pillow's internal safety threshold
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class FileValidationError(HTTPException):
    """Custom HTTP Exception for image validation errors."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


async def validate_and_extract_image_metadata(
    upload_file: UploadFile,
) -> Tuple[ImageMetadataSchema, bytes]:
    """Validate uploaded image file and extract technical metadata in-memory.

    Args:
        upload_file: The FastAPI UploadFile stream.

    Returns:
        Tuple of (ImageMetadataSchema, raw_bytes).

    Raises:
        HTTPException: With appropriate 400, 413, or 415 status code and clear error description.
    """
    if not upload_file or not upload_file.filename:
        raise FileValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was submitted. Please attach an image file.",
        )

    # 1. Sanitize original filename
    sanitized_name = sanitize_filename(upload_file.filename)
    _, ext = os.path.splitext(sanitized_name)
    ext_lower = ext.lower()

    # 2. Check extension whitelist
    if ext_lower not in settings.ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_FILE_EXTENSIONS)
        raise FileValidationError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {allowed}",
        )

    # 3. Read content with size bounding (prevent memory exhaustion)
    # Read chunk-by-chunk up to MAX + 1 byte
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    content_chunks = []
    total_bytes = 0

    while True:
        chunk = await upload_file.read(64 * 1024)  # 64 KB chunks
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise FileValidationError(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File size exceeds the maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            )
        content_chunks.append(chunk)

    if total_bytes == 0:
        raise FileValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    raw_bytes = b"".join(content_chunks)

    # 4. Verify MIME type reported by header or derive from image format
    mime_type = upload_file.content_type or ""
    # Normalizing common variant
    if mime_type.lower() == "image/jpg":
        mime_type = "image/jpeg"

    # 5. Image integrity & dimension parsing via Pillow
    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img.verify()  # Verifies header and stream consistency

        # Re-open for dimension inspection after verify() closes the stream
        with Image.open(io.BytesIO(raw_bytes)) as img:
            width, height = img.size
            img_format = img.format.lower() if img.format else "unknown"

            # Check image dimensions against pixel flood / decompression bomb limits
            if width <= 0 or height <= 0:
                raise FileValidationError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions are invalid (0 or negative).",
                )

            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise FileValidationError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image dimension ({width}x{height}) exceeds maximum allowed limit of {MAX_IMAGE_DIMENSION}px.",
                )

            total_pixels = width * height
            if total_pixels > MAX_IMAGE_PIXELS:
                raise FileValidationError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image resolution ({total_pixels:,} pixels) exceeds safe processing limit of {MAX_IMAGE_PIXELS:,} pixels.",
                )

            # Re-check or infer MIME type based on decoded image format
            format_to_mime = {
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }
            verified_mime = format_to_mime.get(img_format, mime_type)

            if verified_mime not in settings.ALLOWED_IMAGE_TYPES:
                allowed_types = ", ".join(settings.ALLOWED_IMAGE_TYPES)
                raise FileValidationError(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Decoded image format '{img_format}' is not permitted. Allowed MIME types: {allowed_types}",
                )

    except Image.DecompressionBombError as exc:
        raise FileValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image exceeds safe decompression limits (decompression bomb detected).",
        ) from exc
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise FileValidationError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is corrupted or could not be decoded as a valid image.",
        ) from exc

    # 6. Compute in-memory SHA-256 checksum
    file_hash = calculate_sha256(raw_bytes)

    metadata = ImageMetadataSchema(
        file_name=sanitized_name,
        file_size_bytes=total_bytes,
        mime_type=verified_mime,
        image_width=width,
        image_height=height,
        file_hash=file_hash,
    )

    return metadata, raw_bytes
