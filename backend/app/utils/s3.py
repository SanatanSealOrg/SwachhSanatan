"""
S3 utilities for file uploads using boto3.

Provides S3 client initialization and key generation for complaint image uploads.
"""

import boto3
import os
import logging

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Initialize and return boto3 S3 client.

    Uses environment variables for configuration:
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    - AWS_ENDPOINT_URL: Custom endpoint (for LocalStack in dev)
    - AWS_REGION: AWS region (default: us-east-1)

    Returns:
        boto3 S3 client object

    Example:
        >>> s3_client = get_s3_client()
        >>> s3_client.list_buckets()
    """
    try:
        endpoint_url = os.getenv("AWS_ENDPOINT_URL", None)
        region = os.getenv("AWS_REGION", "us-east-1")

        kwargs = {
            "region_name": region,
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "test"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        }

        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", **kwargs)
        logger.debug(f"S3 client initialized with endpoint: {endpoint_url or 'default AWS'}")
        return s3_client

    except Exception as e:
        logger.error(f"Error initializing S3 client: {str(e)}")
        raise


def get_s3_key(complaint_id: str, filename: str) -> str:
    """
    Generate S3 object key for a complaint image.

    Args:
        complaint_id: UUID of complaint
        filename: Original filename

    Returns:
        S3 key path (format: complaints/{complaint_id}/{filename})

    Example:
        >>> key = get_s3_key("123e4567-e89b-12d3-a456-426614174000", "photo.jpg")
        >>> key
        'complaints/123e4567-e89b-12d3-a456-426614174000/photo.jpg'
    """
    return f"complaints/{complaint_id}/{filename}"
