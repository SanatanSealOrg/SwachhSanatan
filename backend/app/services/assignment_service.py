"""
Assignment service for officer routing and task management.

Handles automatic assignment of complaints to available officers,
officer availability tracking, and assignment lifecycle management.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend_models import Assignment, User, Complaint, AssignmentStatus, UserType, ComplaintStatus

logger = logging.getLogger(__name__)


def find_available_officer(db: Session, ward_id: UUID) -> Optional[UUID]:
    """
    Find an available officer in the specified ward.

    Queries for active officers assigned to the ward with fewest pending assignments.
    Implements round-robin-like distribution by selecting officer with lowest pending count.

    Args:
        db: Database session
        ward_id: UUID of ward to find officer for

    Returns:
        UUID of available officer, or None if no officers available

    Example:
        >>> officer_id = find_available_officer(db, ward_uuid)
        >>> officer_id
        UUID('...')
    """
    try:
        # Query officers in ward who are active
        officers = db.query(User).filter(
            User.ward_id == ward_id,
            User.user_type == UserType.officer,
            User.is_active == True
        ).all()

        if not officers:
            logger.warning(f"No available officers found in ward {ward_id}")
            return None

        # If only one officer, return them
        if len(officers) == 1:
            logger.info(f"Single officer found in ward {ward_id}: {officers[0].id}")
            return officers[0].id

        # Otherwise, find officer with fewest pending assignments
        officer_loads = {}
        for officer in officers:
            pending_count = db.query(Assignment).filter(
                Assignment.assigned_to == officer.id,
                Assignment.status == AssignmentStatus.pending
            ).count()
            officer_loads[officer.id] = pending_count

        # Select officer with lowest load
        selected_officer_id = min(officer_loads, key=officer_loads.get)
        logger.info(
            f"Selected officer {selected_officer_id} with {officer_loads[selected_officer_id]} "
            f"pending assignments for ward {ward_id}"
        )
        return selected_officer_id

    except Exception as e:
        logger.error(f"Error finding available officer for ward {ward_id}: {str(e)}")
        return None


def create_assignment(
    db: Session,
    complaint_id: UUID,
    officer_id: UUID
) -> Optional[UUID]:
    """
    Create an assignment record linking complaint to officer.

    Creates Assignment with status=pending, assigned_at=now, due_at=now+24h.
    Immediately commits to database.

    Args:
        db: Database session
        complaint_id: UUID of complaint to assign
        officer_id: UUID of officer to assign to

    Returns:
        UUID of created assignment, or None if creation failed

    Example:
        >>> assignment_id = create_assignment(db, complaint_uuid, officer_uuid)
        >>> assignment_id
        UUID('...')
    """
    try:
        # Check if assignment already exists for this complaint
        existing = db.query(Assignment).filter(
            Assignment.complaint_id == complaint_id
        ).first()

        if existing:
            logger.warning(
                f"Assignment already exists for complaint {complaint_id}: {existing.id}"
            )
            return existing.id

        # Create assignment
        now = datetime.utcnow()
        assignment = Assignment(
            complaint_id=complaint_id,
            assigned_to=officer_id,
            status=AssignmentStatus.pending,
            assigned_at=now,
            due_at=now + timedelta(hours=24)
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        logger.info(
            f"Assignment created: {assignment.id} "
            f"(complaint: {complaint_id}, officer: {officer_id})"
        )
        return assignment.id

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating assignment: {str(e)}")
        return None


def auto_assign_complaint(db: Session, complaint_id: UUID) -> bool:
    """
    Automatically assign complaint to available officer.

    Fetches complaint, determines its ward, finds available officer,
    and creates assignment. Returns False if no officers available.

    Args:
        db: Database session
        complaint_id: UUID of complaint to auto-assign

    Returns:
        True if assignment successful, False otherwise

    Example:
        >>> success = auto_assign_complaint(db, complaint_uuid)
        >>> success
        True
    """
    try:
        # Get complaint
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            logger.warning(f"Complaint {complaint_id} not found for auto-assignment")
            return False

        # Find available officer in complaint's ward
        officer_id = find_available_officer(db, complaint.ward_id)
        if not officer_id:
            logger.warning(
                f"No available officers in ward {complaint.ward_id} for complaint {complaint_id}"
            )
            return False

        # Create assignment
        assignment_id = create_assignment(db, complaint_id, officer_id)
        if not assignment_id:
            logger.error(f"Failed to create assignment for complaint {complaint_id}")
            return False

        # Update complaint status to 'assigned'
        complaint.status = ComplaintStatus.assigned
        complaint.updated_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Complaint {complaint.ticket_number} auto-assigned to officer {officer_id}"
        )
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error in auto_assign_complaint: {str(e)}")
        return False
