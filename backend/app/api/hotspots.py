"""
Hotspot detection endpoint (public).

Runs DBSCAN clustering over active complaints from the last 30 days and
returns AI-detected waste hotspots for the public dashboard map.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend_database import SessionLocal
from backend_models import Ward
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
async def list_hotspots(ward_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    """
    AI-detected waste hotspots: clusters of active complaints (open, assigned,
    in progress) from the last 30 days. No auth, no personal data.
    Optional ward_id filters hotspots by polygon containment — the city-wide
    desk ward therefore sees every hotspot; named wards see only their own.
    """
    try:
        result = metrics_service.compute_hotspots(db)
        if ward_id is not None:
            ward = db.query(Ward).filter(Ward.id == ward_id).first()
            filtered = []
            if ward is not None and ward.geometry is not None:
                for h in result["hotspots"]:
                    point = f"POINT({h['centroid']['lon']} {h['centroid']['lat']})"
                    contained = db.query(
                        func.ST_Within(
                            func.ST_GeomFromText(point, 4326), ward.geometry
                        )
                    ).scalar()
                    if contained:
                        filtered.append(h)
            result = {**result, "hotspots": filtered}
        return result
    except Exception as e:
        logger.error(f"Error computing hotspots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute hotspots",
        )
