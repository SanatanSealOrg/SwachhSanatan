"""
Complaint business logic service for CleanLoop API.

Handles complaint creation, retrieval, filtering, and status updates.
Uses PostGIS for geographic queries.
"""

import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from geoalchemy2 import func
from backend_models import Complaint, Ward, ComplaintStatus, WasteType

logger = logging.getLogger(__name__)


def generate_ticket_number(complaint_id: str) -> str:
    """
    Generate unique ticket number for complaint.

    Args:
        complaint_id: UUID of complaint

    Returns:
        Ticket number (format: CL-{timestamp}{random_4_digits})

    Example:
        >>> ticket = generate_ticket_number("123e4567-e89b-12d3-a456-426614174000")
        >>> ticket.startswith("CL-")
        True
    """
    import random
    import time
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    ticket_number = f"CL-{timestamp}{random_suffix}"
    logger.debug(f"Generated ticket: {ticket_number}")
    return ticket_number


def find_ward_by_location(db: Session, latitude: float, longitude: float) -> Optional[Ward]:
    """
    Find ward containing given GPS coordinates using PostGIS ST_Within.

    Args:
        db: Database session
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Ward object if found, None otherwise

    Example:
        >>> ward = find_ward_by_location(db, 13.0827, 80.2707)
        >>> ward.name
        'Anna Nagar'
    """
    try:
        # Create point from lat/lon
        from geoalchemy2 import Geometry
        point = f"POINT({longitude} {latitude})"

        # Query wards where point is within geometry
        ward = db.query(Ward).filter(
            func.ST_Within(func.ST_GeomFromText(point, 4326), Ward.geometry)
        ).first()

        if ward:
            logger.info(f"Ward found for location ({latitude}, {longitude}): {ward.name}")
        else:
            logger.warning(f"No ward found for location ({latitude}, {longitude})")

        return ward

    except Exception as e:
        logger.error(f"Error finding ward by location: {str(e)}")
        return None


def create_complaint(
    db: Session,
    citizen_id: UUID,
    latitude: float,
    longitude: float,
    description: str,
    image_url: str,
    waste_type: Optional[str] = None,
    severity_score: int = 3,
    ward_id: Optional[UUID] = None
) -> Complaint:
    """
    Create new complaint record in database.

    Args:
        db: Database session
        citizen_id: UUID of citizen creating complaint
        latitude: Latitude of complaint location
        longitude: Longitude of complaint location
        description: Description of waste issue
        image_url: S3 URL of uploaded image
        waste_type: Type of waste ('bin', 'dumping', 'construction', 'biohazard')
        severity_score: Severity 1-5 (default 3)
        ward_id: Optional ward ID (will be auto-detected if not provided)

    Returns:
        Created Complaint object

    Raises:
        ValueError: If complaint creation fails

    Example:
        >>> complaint = create_complaint(
        ...     db=db,
        ...     citizen_id=citizen_uuid,
        ...     latitude=13.0827,
        ...     longitude=80.2707,
        ...     description="Overflowing waste bin",
        ...     image_url="https://s3.../complaint.jpg",
        ...     waste_type="bin",
        ...     severity_score=4
        ... )
        >>> complaint.ticket_number.startswith("CL-")
        True
    """
    try:
        # Auto-detect ward if not provided
        if not ward_id:
            ward = find_ward_by_location(db, latitude, longitude)
            if not ward:
                raise ValueError("Could not determine ward for given location")
            ward_id = ward.id
        else:
            # Verify ward exists
            ward = db.query(Ward).filter(Ward.id == ward_id).first()
            if not ward:
                raise ValueError(f"Ward {ward_id} not found")

        # Create location point
        from geoalchemy2 import func
        point = f"POINT({longitude} {latitude})"

        # Generate ticket number
        import uuid
        temp_id = str(uuid.uuid4())
        ticket_number = generate_ticket_number(temp_id)

        # Create complaint
        complaint = Complaint(
            ticket_number=ticket_number,
            citizen_id=citizen_id,
            ward_id=ward_id,
            location=func.ST_GeomFromText(point, 4326),
            description=description,
            waste_type=waste_type,
            severity_score=severity_score,
            image_urls=[image_url] if image_url else [],
            status=ComplaintStatus.open,
            created_at=datetime.utcnow()
        )

        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        logger.info(f"Complaint created: {complaint.ticket_number} (citizen: {citizen_id})")

        # Trigger AI classification for image
        try:
            from backend.app.services import ai_service
            classification = ai_service.classify_image_with_openai(image_url)
            ai_service.update_complaint_with_classification(db, complaint.id, classification)
            logger.info(f"AI classification completed for complaint {complaint.ticket_number}")
        except Exception as e:
            logger.error(f"AI classification failed for complaint {complaint.ticket_number}: {str(e)}")

        # Auto-assign to available officer
        try:
            from backend.app.services import assignment_service
            assignment_service.auto_assign_complaint(db, complaint.id)
            logger.info(f"Auto-assignment completed for complaint {complaint.ticket_number}")
        except Exception as e:
            logger.error(f"Auto-assignment failed for complaint {complaint.ticket_number}: {str(e)}")

        return complaint

    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error creating complaint: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating complaint: {str(e)}")
        raise ValueError(f"Failed to create complaint: {str(e)}")


def get_complaint_by_id(db: Session, complaint_id: UUID) -> Optional[Complaint]:
    """
    Retrieve complaint by ID.

    Args:
        db: Database session
        complaint_id: UUID of complaint

    Returns:
        Complaint object if found, None otherwise

    Example:
        >>> complaint = get_complaint_by_id(db, complaint_uuid)
        >>> complaint.ticket_number
        'CL-...'
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        return complaint
    except Exception as e:
        logger.error(f"Error retrieving complaint {complaint_id}: {str(e)}")
        return None


def list_complaints_by_ward(
    db: Session,
    ward_id: UUID,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Complaint]:
    """
    List complaints for a ward, optionally filtered by status.

    Args:
        db: Database session
        ward_id: UUID of ward
        status: Optional status filter ('open', 'assigned', 'in_progress', 'resolved', 'rejected')
        limit: Max complaints to return (default 50)
        offset: Skip N complaints (for pagination, default 0)

    Returns:
        List of Complaint objects sorted by created_at DESC

    Example:
        >>> complaints = list_complaints_by_ward(db, ward_uuid, status='open', limit=20)
        >>> len(complaints)
        20
    """
    try:
        query = db.query(Complaint).filter(Complaint.ward_id == ward_id)

        if status:
            query = query.filter(Complaint.status == status)

        complaints = query.order_by(Complaint.created_at.desc()).limit(limit).offset(offset).all()
        logger.info(f"Retrieved {len(complaints)} complaints for ward {ward_id}")
        return complaints

    except Exception as e:
        logger.error(f"Error listing complaints for ward {ward_id}: {str(e)}")
        return []


def update_complaint_status(
    db: Session,
    complaint_id: UUID,
    new_status: str,
    notes: Optional[str] = None
) -> Optional[Complaint]:
    """
    Update complaint status.

    Args:
        db: Database session
        complaint_id: UUID of complaint
        new_status: New status ('open', 'assigned', 'in_progress', 'resolved', 'rejected')
        notes: Optional notes about status change

    Returns:
        Updated Complaint object, or None if not found

    Raises:
        ValueError: If invalid status provided

    Example:
        >>> complaint = update_complaint_status(
        ...     db,
        ...     complaint_uuid,
        ...     "in_progress",
        ...     notes="Cleaning crew assigned"
        ... )
        >>> complaint.status
        'in_progress'
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            logger.warning(f"Complaint {complaint_id} not found for status update")
            return None

        # Validate status
        valid_statuses = [cs.value for cs in ComplaintStatus]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()

        # Set resolved_at if status is resolved
        if new_status == ComplaintStatus.resolved:
            complaint.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(complaint)

        logger.info(f"Complaint {complaint.ticket_number} status updated to: {new_status}")
        return complaint

    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error updating complaint: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating complaint status: {str(e)}")
        raise ValueError(f"Failed to update complaint: {str(e)}")


def get_complaint_count_by_ward(
    db: Session,
    ward_id: UUID,
    status: Optional[str] = None
) -> int:
    """
    Get count of complaints for a ward.

    Args:
        db: Database session
        ward_id: UUID of ward
        status: Optional status filter

    Returns:
        Number of complaints

    Example:
        >>> count = get_complaint_count_by_ward(db, ward_uuid, status='open')
        >>> count
        42
    """
    try:
        query = db.query(Complaint).filter(Complaint.ward_id == ward_id)
        if status:
            query = query.filter(Complaint.status == status)
        return query.count()
    except Exception as e:
        logger.error(f"Error counting complaints: {str(e)}")
        return 0
