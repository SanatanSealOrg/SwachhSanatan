"""
Complaint API routes for CleanLoop.

Provides endpoints for submitting complaints with images, retrieving complaint details,
listing complaints by ward, and updating complaint status.
"""

import io
import logging
import uuid as uuid_module
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend_models import User, Complaint
from backend.app.services import ai_service
from backend_schemas import ComplaintCreateRequest, ComplaintResponse, ComplaintUpdateRequest
from backend.app.dependencies import get_db, get_current_user, get_current_officer
from backend.app.services import complaint_service
from backend.app.services import image_service
from backend.app.utils.validators import (
    validate_gps_coordinates,
    validate_file_size,
    validate_file_type,
    validate_waste_type,
    validate_severity_score
)
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["complaints"])


def _complaint_to_dict(complaint: Complaint) -> dict:
    """Convert Complaint model to response dictionary."""
    return {
        "id": str(complaint.id),
        "ticket_number": complaint.ticket_number,
        "citizen_id": str(complaint.citizen_id),
        "ward_id": str(complaint.ward_id),
        "status": complaint.status.value if hasattr(complaint.status, 'value') else complaint.status,
        "description": complaint.description,
        "waste_type": complaint.waste_type.value if hasattr(complaint.waste_type, 'value') else complaint.waste_type,
        "severity_score": complaint.severity_score,
        "image_urls": complaint.image_urls or [],
        "ai_waste_type": complaint.ai_waste_type,
        "ai_confidence": complaint.ai_confidence,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
        "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
    }


@router.post("/complaints/analyze", response_model=dict)
async def analyze_complaint_photo(
    file: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a waste photo with AI and return a drafted complaint for review.

    The image is processed and uploaded once to a staging location; the returned
    image_key can be passed to POST /api/complaints to attach the same image
    without re-uploading.

    Returns:
        {
            "draft": {waste_type, severity, severity_reasoning, confidence,
                      title, description, hazards, is_waste_visible, source},
            "image": {"url": "...", "key": "complaints/drafts/<uuid>/<file>.jpg"}
        }
    """
    is_valid, error_msg = validate_file_type(file.filename)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    file_content = await file.read()
    is_valid, error_msg = validate_file_size(len(file_content), max_mb=5)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    try:
        clean_image = image_service.strip_exif_metadata(file_content)
        compressed_image = image_service.compress_image(clean_image)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image processing failed: {str(e)}"
        )

    try:
        draft_id = f"drafts/{uuid_module.uuid4()}"
        s3_url = image_service.upload_image_to_s3(
            file_bytes=compressed_image,
            filename=file.filename,
            complaint_id=draft_id,
        )
        s3_key = f"complaints/{draft_id}/{file.filename}"
    except ValueError as e:
        logger.error(f"Draft image upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image. Please try again."
        )

    # Never raises — falls back to a mock draft on any AI failure
    draft = ai_service.analyze_waste_image(compressed_image)

    logger.info(
        f"Photo analyzed for user {current_user.id}: "
        f"{draft.get('waste_type')} (source: {draft.get('source')})"
    )
    return {"draft": draft, "image": {"url": s3_url, "key": s3_key}}


@router.get("/complaints/map", response_model=dict)
async def complaints_map_feed(db: Session = Depends(get_db)):
    """
    Public map feed: complaint points from the last 30 days (max 500).

    No auth and no personal data — powers the public dashboard map.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        rows = (
            db.query(
                Complaint.id,
                Complaint.ticket_number,
                Complaint.status,
                Complaint.waste_type,
                Complaint.severity_score,
                Complaint.created_at,
                Complaint.image_urls,
                func.ST_Y(Complaint.location).label("lat"),
                func.ST_X(Complaint.location).label("lon"),
            )
            .filter(Complaint.created_at >= cutoff)
            .order_by(Complaint.created_at.desc())
            .limit(500)
            .all()
        )
        points = [
            {
                "id": str(r.id),
                "ticket_number": r.ticket_number,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "waste_type": (
                    r.waste_type.value if hasattr(r.waste_type, "value") else r.waste_type
                ),
                "severity_score": r.severity_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "lat": r.lat,
                "lon": r.lon,
                "thumbnail_url": (r.image_urls or [None])[0],
            }
            for r in rows
        ]
        return {"complaints": points, "count": len(points)}
    except Exception as e:
        logger.error(f"Error building map feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load map data"
        )


@router.post("/complaints", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    waste_type: Optional[str] = Form(None),
    severity_score: Optional[int] = Form(3),
    file: UploadFile = File(None),
    image_key: Optional[str] = Form(None),
    ai_waste_type: Optional[str] = Form(None),
    ai_confidence: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new complaint with photo upload.

    Accepts multipart FormData with:
    - description: Description of waste issue (required)
    - latitude: GPS latitude -90 to 90 (required)
    - longitude: GPS longitude -180 to 180 (required)
    - waste_type: Type of waste - 'bin', 'dumping', 'construction', 'biohazard' (optional)
    - severity_score: Severity 1-5 (default 3, optional)
    - file: Image file (jpg, jpeg, png, gif, webp) max 5MB — required unless image_key given
    - image_key: staged draft image key from POST /complaints/analyze (reuses that
      upload instead of a new file)
    - ai_waste_type / ai_confidence: AI draft metadata to persist on the complaint

    Returns:
        ComplaintResponse with ticket_number, complaint_id, status, ward_id

    Raises:
        HTTPException 400: If validation fails (invalid GPS, unsupported file, etc.)
        HTTPException 401: If not authenticated
        HTTPException 500: If server error

    Example (cURL):
        curl -X POST http://localhost:8000/api/complaints \\
          -H "Authorization: Bearer TOKEN" \\
          -F "description=Overflowing waste bin at corner" \\
          -F "latitude=13.0827" \\
          -F "longitude=80.2707" \\
          -F "waste_type=bin" \\
          -F "severity_score=4" \\
          -F "file=@photo.jpg"

        Response 201:
        {
            "id": "uuid",
            "ticket_number": "CL-16892348521234",
            "citizen_id": "uuid",
            "ward_id": "uuid",
            "status": "open",
            "image_urls": ["https://s3.../complaint.jpg"],
            "created_at": "2024-01-15T10:30:00"
        }
    """
    try:
        # Validate GPS coordinates
        is_valid, error_msg = validate_gps_coordinates(latitude, longitude)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Either a fresh photo or a staged draft image is required
        if file is None and not image_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either a photo file or an image_key from /complaints/analyze is required"
            )
        if image_key and not image_key.startswith("complaints/drafts/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image_key"
            )

        file_content = None
        if file is not None:
            # Validate file type
            is_valid, error_msg = validate_file_type(file.filename)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            # Read file content
            file_content = await file.read()

            # Validate file size (5MB limit)
            is_valid, error_msg = validate_file_size(len(file_content), max_mb=5)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

        # Validate waste_type if provided
        if waste_type:
            is_valid, error_msg = validate_waste_type(waste_type)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

        # Validate severity_score if provided
        is_valid, error_msg = validate_severity_score(severity_score)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        try:
            compressed_image = None
            if file_content is not None:
                # Fresh upload: strip EXIF + compress
                clean_image = image_service.strip_exif_metadata(file_content)
                compressed_image = image_service.compress_image(clean_image)

            # Create complaint record (will auto-detect ward)
            complaint = complaint_service.create_complaint(
                db=db,
                citizen_id=current_user.id,
                latitude=latitude,
                longitude=longitude,
                description=description,
                image_url="",  # Will update after S3 upload/promotion
                waste_type=waste_type,
                severity_score=severity_score,
                ai_waste_type=ai_waste_type,
                ai_confidence=ai_confidence
            )

            if compressed_image is not None:
                # Upload fresh photo to S3
                filename = f"{complaint.id}_{file.filename}"
                s3_url = image_service.upload_image_to_s3(
                    file_bytes=compressed_image,
                    filename=filename,
                    complaint_id=str(complaint.id),
                )
            else:
                # Reuse the image already staged by /complaints/analyze
                s3_url = image_service.promote_draft_image(image_key, str(complaint.id))

            # Update complaint with image URL
            complaint.image_urls = [s3_url]
            db.commit()
            db.refresh(complaint)

            logger.info(f"Complaint created with S3 image: {complaint.ticket_number}")
            return _complaint_to_dict(complaint)

        except ValueError as e:
            logger.error(f"Image processing error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image processing failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating complaint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create complaint. Please try again."
        )


@router.get("/complaints/{complaint_id}", response_model=dict)
async def get_complaint(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complaint details by ID.

    Returns full complaint information including image URLs, assignment status, and AI metadata.

    Args:
        complaint_id: UUID of complaint
        current_user: Authenticated user (required)

    Returns:
        ComplaintResponse with full complaint details

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 404: If complaint not found

    Example (cURL):
        GET /api/complaints/123e4567-e89b-12d3-a456-426614174000
        Authorization: Bearer TOKEN

        Response 200:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "ticket_number": "CL-...",
            "citizen_id": "...",
            "ward_id": "...",
            "status": "open",
            "description": "...",
            "image_urls": ["https://s3.../..."],
            "created_at": "2024-01-15T10:30:00"
        }
    """
    try:
        complaint = complaint_service.get_complaint_by_id(db, complaint_id)

        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found"
            )

        return _complaint_to_dict(complaint)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving complaint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve complaint"
        )


@router.get("/complaints", response_model=dict)
async def list_complaints(
    ward_id: UUID,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List complaints for a ward with optional status filtering.

    Returns paginated list of complaints sorted by created_at (newest first).
    Officers can only see complaints from their assigned ward.

    Args:
        ward_id: Ward ID (required)
        status: Optional status filter - 'open', 'assigned', 'in_progress', 'resolved', 'rejected'
        limit: Max complaints per page (default 50, max 100)
        offset: Skip N complaints for pagination (default 0)
        current_user: Authenticated user (required)

    Returns:
        {
            "complaints": [ComplaintResponse, ...],
            "total": int,
            "limit": int,
            "offset": int
        }

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 400: If invalid status provided
        HTTPException 403: If officer accessing different ward

    Example (cURL):
        GET /api/complaints?ward_id=UUID&status=open&limit=20
        Authorization: Bearer TOKEN

        Response 200:
        {
            "complaints": [...],
            "total": 42,
            "limit": 20,
            "offset": 0
        }
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        # Validate status if provided
        if status:
            valid_statuses = ['open', 'assigned', 'in_progress', 'resolved', 'rejected']
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )

        # For officers, verify they belong to the ward
        if current_user.user_type == 'officer':
            if str(current_user.ward_id) != str(ward_id):
                logger.warning(
                    f"Officer {current_user.id} attempted to access ward {ward_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view complaints from your assigned ward"
                )

        # Fetch complaints
        complaints = complaint_service.list_complaints_by_ward(
            db=db,
            ward_id=ward_id,
            status=status,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination
        total = complaint_service.get_complaint_count_by_ward(db, ward_id, status)

        return {
            "complaints": [_complaint_to_dict(c) for c in complaints],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing complaints: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list complaints"
        )


@router.patch("/complaints/{complaint_id}", response_model=dict)
async def update_complaint_status(
    complaint_id: UUID,
    request: ComplaintUpdateRequest,
    current_officer: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Update complaint status (officer only).

    Allows officers to update complaint status and add notes.
    Only officers can perform this action. Officers can only update complaints from their ward.

    Args:
        complaint_id: UUID of complaint
        request: ComplaintUpdateRequest with status and optional notes
        current_officer: Authenticated officer user (required)

    Returns:
        Updated ComplaintResponse

    Raises:
        HTTPException 401: If not authenticated or not an officer
        HTTPException 403: If officer accessing different ward
        HTTPException 404: If complaint not found
        HTTPException 400: If invalid status

    Example (cURL):
        PATCH /api/complaints/123e4567-e89b-12d3-a456-426614174000
        Authorization: Bearer TOKEN
        Content-Type: application/json

        {
            "status": "in_progress",
            "notes": "Cleaning crew assigned"
        }

        Response 200:
        {
            "id": "...",
            "status": "in_progress",
            "updated_at": "2024-01-15T10:35:00",
            ...
        }
    """
    try:
        # Get complaint
        complaint = complaint_service.get_complaint_by_id(db, complaint_id)

        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found"
            )

        # Verify officer belongs to complaint's ward
        if str(current_officer.ward_id) != str(complaint.ward_id):
            logger.warning(
                f"Officer {current_officer.id} attempted to update complaint from ward {complaint.ward_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update complaints from your assigned ward"
            )

        # Update status
        updated_complaint = complaint_service.update_complaint_status(
            db=db,
            complaint_id=complaint_id,
            new_status=request.status,
            notes=request.notes
        )

        logger.info(f"Complaint {complaint.ticket_number} updated by officer {current_officer.id}")
        return _complaint_to_dict(updated_complaint)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating complaint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update complaint"
        )
