"""
Image processing service for CleanLoop API.

Handles image compression, EXIF metadata removal, thumbnail generation, and S3 uploads.
"""

import io
import os
import logging
from PIL import Image
from PIL.Image import Resampling
from botocore.exceptions import ClientError
from backend.app.utils.s3 import get_s3_client, get_s3_key

logger = logging.getLogger(__name__)


def compress_image(
    image_bytes: bytes,
    max_width: int = 1920,
    max_height: int = 1920,
    quality: int = 85
) -> bytes:
    """
    Compress image to specified dimensions and quality.

    Args:
        image_bytes: Image file content as bytes
        max_width: Maximum width in pixels (default 1920)
        max_height: Maximum height in pixels (default 1920)
        quality: JPEG quality 1-100 (default 85)

    Returns:
        Compressed image as bytes (<2MB target)

    Raises:
        ValueError: If image is invalid

    Example:
        >>> with open("large_photo.jpg", "rb") as f:
        ...     compressed = compress_image(f.read())
        >>> len(compressed) < len(open("large_photo.jpg", "rb").read())
        True
    """
    try:
        # Open image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if needed
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        # Resize if larger than max dimensions
        img.thumbnail((max_width, max_height), Resampling.LANCZOS)

        # Save compressed
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        compressed_bytes = output.getvalue()

        original_size_kb = len(image_bytes) / 1024
        compressed_size_kb = len(compressed_bytes) / 1024
        logger.info(f"Image compressed: {original_size_kb:.2f}KB → {compressed_size_kb:.2f}KB")

        return compressed_bytes

    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        raise ValueError(f"Failed to compress image: {str(e)}")


def strip_exif_metadata(image_bytes: bytes) -> bytes:
    """
    Remove EXIF metadata from image using PIL.

    Args:
        image_bytes: Image file content as bytes

    Returns:
        Image bytes without EXIF metadata

    Raises:
        ValueError: If image is invalid

    Example:
        >>> with open("photo_with_metadata.jpg", "rb") as f:
        ...     clean = strip_exif_metadata(f.read())
        >>> len(clean) <= len(open("photo_with_metadata.jpg", "rb").read())
        True
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Create new image without metadata
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)

        output = io.BytesIO()
        image_without_exif.save(output, format="JPEG")
        clean_bytes = output.getvalue()

        logger.info("EXIF metadata stripped from image")
        return clean_bytes

    except Exception as e:
        logger.error(f"Error stripping EXIF: {str(e)}")
        raise ValueError(f"Failed to strip EXIF metadata: {str(e)}")


def generate_thumbnail(image_bytes: bytes, size: tuple = (200, 200)) -> bytes:
    """
    Generate thumbnail from image.

    Args:
        image_bytes: Image file content as bytes
        size: Thumbnail dimensions (default 200x200)

    Returns:
        Thumbnail image bytes in JPEG format

    Raises:
        ValueError: If image is invalid

    Example:
        >>> with open("photo.jpg", "rb") as f:
        ...     thumb = generate_thumbnail(f.read(), size=(150, 150))
        >>> len(thumb) < len(f.read())
        True
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if needed
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        img.thumbnail(size, Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        thumb_bytes = output.getvalue()

        logger.info(f"Thumbnail generated: {size}")
        return thumb_bytes

    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        raise ValueError(f"Failed to generate thumbnail: {str(e)}")


def _build_public_url(bucket: str, s3_key: str) -> str:
    """
    Build a browser-reachable URL for an S3 object.

    AWS_PUBLIC_ENDPOINT_URL overrides AWS_ENDPOINT_URL for URL construction —
    needed when the backend reaches LocalStack via a docker-internal hostname
    (http://localstack:4566) that browsers cannot resolve.
    """
    endpoint_url = os.getenv("AWS_PUBLIC_ENDPOINT_URL") or os.getenv("AWS_ENDPOINT_URL")
    if endpoint_url:
        return f"{endpoint_url}/{bucket}/{s3_key}"
    region = os.getenv("AWS_REGION", "us-east-1")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


def promote_draft_image(image_key: str, complaint_id: str, bucket: str = None) -> str:
    """
    Move a staged draft image (complaints/drafts/<uuid>/<file>) to its final
    complaint location and return the final public URL.

    Args:
        image_key: S3 key of the draft object (must be under complaints/drafts/)
        complaint_id: UUID of the created complaint
        bucket: S3 bucket (env default if not provided)

    Raises:
        ValueError: If the key is not a draft key or the S3 operation fails
    """
    if not image_key.startswith("complaints/drafts/"):
        raise ValueError("Invalid draft image key")
    try:
        if bucket is None:
            bucket = os.getenv("AWS_S3_BUCKET") or os.getenv("S3_BUCKET", "cleanloop-complaints")
        s3_client = get_s3_client()
        filename = image_key.rsplit("/", 1)[-1]
        final_key = get_s3_key(str(complaint_id), filename)
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": image_key},
            Key=final_key,
        )
        s3_client.delete_object(Bucket=bucket, Key=image_key)
        logger.info(f"Draft image promoted: {image_key} -> {final_key}")
        return _build_public_url(bucket, final_key)
    except ClientError as e:
        logger.error(f"Draft promotion failed: {str(e)}")
        raise ValueError(f"Failed to attach draft image: {str(e)}")


def upload_image_to_s3(
    file_bytes: bytes,
    filename: str,
    complaint_id: str,
    bucket: str = None
) -> str:
    """
    Upload image to S3 bucket and return URL.

    Args:
        file_bytes: Image file content as bytes
        filename: Original filename (with extension)
        complaint_id: UUID of complaint (for S3 key generation)
        bucket: S3 bucket name (uses S3_BUCKET env var if not provided)

    Returns:
        S3 URL of uploaded image

    Raises:
        ValueError: If upload fails

    Example:
        >>> with open("photo.jpg", "rb") as f:
        ...     url = upload_image_to_s3(f.read(), "photo.jpg", "complaint-123")
        >>> url.startswith("https://")
        True
    """
    try:
        if bucket is None:
            bucket = os.getenv("AWS_S3_BUCKET") or os.getenv("S3_BUCKET", "cleanloop-complaints")

        s3_client = get_s3_client()
        s3_key = get_s3_key(complaint_id, filename)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType="image/jpeg"
        )

        url = _build_public_url(bucket, s3_key)

        logger.info(f"Image uploaded to S3: {s3_key}")
        return url

    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}")
        raise ValueError(f"Failed to upload image to S3: {str(e)}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise ValueError(f"Failed to upload image: {str(e)}")
