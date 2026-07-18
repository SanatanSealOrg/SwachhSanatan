"""
Assignment API routes for CleanLoop.

Provides endpoints for officers to retrieve their task list,
view assignment details, and update assignment status.
"""

import logging
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend_models import User, Assignment, Complaint, AssignmentStatus, ComplaintStatus
from backend_schemas import AssignmentResponse, AssignmentUpdateRequest, ComplaintResponse
from backend.app.dependencies import get_db, get_current_user, get_current_officer
from backend.app.services import assignment_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assignments"])


def _assignment_to_dict(assignment: Assignment, complaint: Optional[Complaint] = None) -> dict:
    """Convert Assignment model to response dictionary."""
    return {
        "id": str(assignment.id),
        "complaint_id": str(assignment.complaint_id),
        "assigned_to": str(assignment.assigned_to),
        "status": assignment.status.value if hasattr(assignment.status, 'value') else assignment.status,
        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
        "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None,
        "verified": assignment.verified,
        "completion_image_url": assignment.completion_image_url,
        "notes": assignment.notes,
        "complaint": _complaint_to_dict(complaint) if complaint else None
    }


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


@router.get("/assignments", response_model=dict, status_code=status.HTTP_200_OK)
async def list_assignments(
    officer_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve assignments for an officer.

    Officers can only view their own assignments. Admins can view assignments for any officer.
    Supports filtering by status: pending, accepted, in_progress, completed, escalated

    Query Parameters:
    - officer_id: UUID of officer (required for non-officers, optional for admins)
    - status: Filter by assignment status (optional)
    - limit: Max results (default 50, max 100)
    - offset: Skip N results for pagination (default 0)

    Returns:
        Dictionary with:
        - total: Total count of matching assignments
        - limit: Pagination limit
        - offset: Pagination offset
        - items: List of assignments with complaint details

    Raises:
        HTTPException 400: If officer_id not provided for non-admin users
        HTTPException 403: If non-admin officer tries to view other's assignments
        HTTPException 401: If not authenticated

    Example:
        GET /api/assignments?officer_id=<uuid>&status=pending&limit=20
    """
    try:
        # Determine which officer to query
        target_officer_id = officer_id

        # If no officer_id specified, use current user's ID if they're an officer
        if not target_officer_id:
            if current_user.user_type.value == "officer":
                target_officer_id = current_user.id
            elif current_user.user_type.value == "admin":
                # Admin must specify officer_id or we return 400
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="officer_id query parameter required"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only officers and admins can view assignments"
                )

        # Access control: non-admin officers can only view their own assignments
        if current_user.user_type.value == "officer" and current_user.id != target_officer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other officers' assignments"
            )

        # Build query
        query = db.query(Assignment).filter(Assignment.assigned_to == target_officer_id)

        # Apply status filter if provided
        if status_filter:
            valid_statuses = [s.value for s in AssignmentStatus]
            if status_filter not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            query = query.filter(Assignment.status == status_filter)

        # Get total count
        total = query.count()

        # Apply pagination and fetch
        assignments = query.order_by(Assignment.assigned_at.desc()).limit(limit).offset(offset).all()

        # Fetch complaints for each assignment
        assignment_dicts = []
        for assignment in assignments:
            complaint = db.query(Complaint).filter(Complaint.id == assignment.complaint_id).first()
            assignment_dicts.append(_assignment_to_dict(assignment, complaint))

        logger.info(
            f"Retrieved {len(assignments)} assignments for officer {target_officer_id} "
            f"(total: {total}, status: {status_filter})"
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": assignment_dicts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assignments"
        )


@router.get("/assignments/{assignment_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve full details of a specific assignment.

    Returns assignment with linked complaint details. Officers can only
    view their own assignments.

    Path Parameters:
    - assignment_id: UUID of assignment

    Returns:
        Assignment object with full complaint details

    Raises:
        HTTPException 404: If assignment not found
        HTTPException 403: If officer tries to view assignment not assigned to them
        HTTPException 401: If not authenticated

    Example:
        GET /api/assignments/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        # Fetch assignment
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {assignment_id} not found"
            )

        # Access control: officers can only view their own assignments
        if current_user.user_type.value == "officer" and current_user.id != assignment.assigned_to:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view assignment not assigned to you"
            )

        # Fetch complaint
        complaint = db.query(Complaint).filter(Complaint.id == assignment.complaint_id).first()

        logger.info(f"Retrieved assignment {assignment_id}")
        return _assignment_to_dict(assignment, complaint)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assignment"
        )


@router.patch("/assignments/{assignment_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_assignment(
    assignment_id: UUID,
    request: AssignmentUpdateRequest,
    current_officer: User = Depends(get_current_officer),
    db: Session = Depends(get_db)
):
    """
    Update assignment status (officer-only action).

    Officers can update their assignments from pending→accepted→in_progress→completed/escalated.

    Path Parameters:
    - assignment_id: UUID of assignment

    Request Body:
    - status: New status (required) - one of: accepted, in_progress, completed, escalated
    - notes: Optional notes about status change (max 500 chars)

    Returns:
        Updated assignment object

    Raises:
        HTTPException 403: If officer doesn't own the assignment
        HTTPException 404: If assignment not found
        HTTPException 400: If invalid status transition
        HTTPException 401: If not authenticated as officer

    Example:
        PATCH /api/assignments/550e8400-e29b-41d4-a716-446655440000
        {
            "status": "in_progress",
            "notes": "Cleaning crew has arrived at location"
        }
    """
    try:
        # Fetch assignment
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {assignment_id} not found"
            )

        # Access control: officer must own assignment
        if current_officer.id != assignment.assigned_to:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update assignment not assigned to you"
            )

        # Validate status
        valid_statuses = [s.value for s in AssignmentStatus]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Validate status transition
        current_status = assignment.status.value if hasattr(assignment.status, 'value') else assignment.status
        valid_transitions = {
            AssignmentStatus.pending.value: [AssignmentStatus.accepted.value, AssignmentStatus.escalated.value],
            AssignmentStatus.accepted.value: [AssignmentStatus.in_progress.value, AssignmentStatus.escalated.value],
            AssignmentStatus.in_progress.value: [AssignmentStatus.completed.value, AssignmentStatus.escalated.value],
            AssignmentStatus.completed.value: [],
            AssignmentStatus.escalated.value: []
        }

        if request.status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {current_status} to {request.status}"
            )

        # Update assignment
        assignment.status = request.status
        assignment.notes = request.notes
        assignment.updated_at = datetime.utcnow()

        # Set completed_at if transitioning to completed
        if request.status == AssignmentStatus.completed.value:
            assignment.completed_at = datetime.utcnow()

            # Update complaint status to in_progress (or resolved if appropriate)
            complaint = db.query(Complaint).filter(Complaint.id == assignment.complaint_id).first()
            if complaint:
                complaint.status = ComplaintStatus.in_progress
                complaint.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assignment)

        logger.info(
            f"Assignment {assignment_id} status updated to {request.status} by officer {current_officer.id}"
        )

        # Fetch complaint for response
        complaint = db.query(Complaint).filter(Complaint.id == assignment.complaint_id).first()
        return _assignment_to_dict(assignment, complaint)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assignment"
        )
