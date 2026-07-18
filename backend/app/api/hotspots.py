"""
Hotspot detection endpoint (public).

Runs DBSCAN clustering over active complaints from the last 30 days and
returns AI-detected waste hotspots for the public dashboard map.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend_database import SessionLocal
from backend.app.services import metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["hotspots"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/hotspots", response_model=dict)
async def list_hotspots(db: Session = Depends(get_db)):
    """
    AI-detected waste hotspots: clusters of active complaints (open, assigned,
    in progress) from the last 30 days. No auth, no personal data.
    """
    try:
        return metrics_service.compute_hotspots(db)
    except Exception as e:
        logger.error(f"Error computing hotspots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute hotspots",
        )
