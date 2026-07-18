"""
Validators for GPS coordinates, file sizes, and file types.

Provides validation functions for geographic coordinates, file uploads, and input validation.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported image file extensions
SUPPORTED_IMAGE_TYPES = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def validate_gps_coordinates(latitude: float, longitude: float) -> tuple:
    """
    Validate GPS coordinates are within valid ranges.

    Args:
        latitude: Latitude value (-90 to 90)
        longitude: Longitude value (-180 to 180)

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_gps_coordinates(13.0827, 80.2707)
        (True, '')
        >>> validate_gps_coordinates(91, 80)
        (False, 'Latitude must be between -90 and 90')
    """
    try:
        lat = float(latitude)
        lon = float(longitude)

        if lat < -90 or lat > 90:
            return False, "Latitude must be between -90 and 90"

        if lon < -180 or lon > 180:
            return False, "Longitude must be between -180 and 180"

        return True, ""

    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid coordinate format: {str(e)}")
        return False, "Coordinates must be numeric values"


def validate_file_size(file_size: int, max_mb: int = 5) -> tuple:
    """
    Validate file size does not exceed maximum.

    Args:
        file_size: File size in bytes
        max_mb: Maximum allowed size in megabytes (default 5MB)

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_file_size(1024 * 1024 * 3)  # 3MB
        (True, '')
        >>> validate_file_size(1024 * 1024 * 10)  # 10MB
        (False, 'File size must not exceed 5 MB')
    """
    try:
        max_bytes = max_mb * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File size must not exceed {max_mb} MB"
        if file_size <= 0:
            return False, "File size must be greater than 0 bytes"
        return True, ""
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid file size: {str(e)}")
        return False, "File size must be a valid number"


def validate_file_type(filename: str) -> tuple:
    """
    Validate file is a supported image type.

    Args:
        filename: Original filename with extension

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_file_type("photo.jpg")
        (True, '')
        >>> validate_file_type("document.pdf")
        (False, 'File type must be one of: jpg, jpeg, png, gif, webp')
    """
    try:
        if not filename:
            return False, "Filename cannot be empty"

        ext = Path(filename).suffix.lstrip('.').lower()

        if ext not in SUPPORTED_IMAGE_TYPES:
            supported = ', '.join(sorted(SUPPORTED_IMAGE_TYPES))
            return False, f"File type must be one of: {supported}"

        return True, ""

    except Exception as e:
        logger.warning(f"Error validating file type: {str(e)}")
        return False, "Invalid filename format"


def validate_waste_type(waste_type: str) -> tuple:
    """
    Validate waste type is one of the supported values.

    Args:
        waste_type: Waste type string

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_waste_type("bin")
        (True, '')
        >>> validate_waste_type("invalid_type")
        (False, 'Waste type must be one of: bin, dumping, construction, biohazard')
    """
    supported_types = {'bin', 'dumping', 'construction', 'biohazard'}

    if waste_type not in supported_types:
        supported = ', '.join(sorted(supported_types))
        return False, f"Waste type must be one of: {supported}"

    return True, ""


def validate_severity_score(severity_score: int) -> tuple:
    """
    Validate severity score is within valid range.

    Args:
        severity_score: Severity score (1-5)

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_severity_score(3)
        (True, '')
        >>> validate_severity_score(10)
        (False, 'Severity score must be between 1 and 5')
    """
    try:
        score = int(severity_score)
        if score < 1 or score > 5:
            return False, "Severity score must be between 1 and 5"
        return True, ""
    except (TypeError, ValueError):
        return False, "Severity score must be a valid integer"
