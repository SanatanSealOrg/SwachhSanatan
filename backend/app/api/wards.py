"""
Ward listing and public metrics endpoints.

These are public (no auth): the ward list feeds dropdowns in the frontend,
and the metrics endpoint powers the public dashboard.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend_database import SessionLocal
from backend_models import Ward, Complaint, ComplaintStatus
from backend.app.services import metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["wards"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/wards", response_model=dict)
async def list_wards(db: Session = Depends(get_db)):
    """List all wards (public). Used for ward pickers in the frontend."""
    try:
        wards = db.query(Ward).order_by(Ward.ward_number).all()
        return {
            "wards": [
                {
                    "id": str(w.id),
                    "name": w.name,
                    "ward_number": w.ward_number,
                    "population": w.population,
                }
                for w in wards
            ]
        }
    except Exception as e:
        logger.error(f"Error listing wards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list wards",
        )


@router.get("/wards/geojson", response_model=dict)
async def wards_geojson(include_dev: bool = False, db: Session = Depends(get_db)):
    """
    Ward polygons as a GeoJSON FeatureCollection (public) — powers the
    dashboard map. The city-wide "(Dev)" desk ward is excluded by default so
    it doesn't blanket the public map; officer views pass include_dev=true.
    """
    try:
        query = db.query(Ward, func.ST_AsGeoJSON(Ward.geometry)).filter(
            Ward.geometry.isnot(None)
        )
        if not include_dev:
            query = query.filter(~Ward.name.like("%(Dev)"))
        rows = query.order_by(Ward.ward_number).all()
        features = [
            {
                "type": "Feature",
                "geometry": json.loads(geom),
                "properties": {
                    "id": str(w.id),
                    "name": w.name,
                    "ward_number": w.ward_number,
                    "population": w.population,
                },
            }
            for w, geom in rows
        ]
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        logger.error(f"Error building ward geojson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load ward boundaries",
        )


@router.get("/metrics/wards", response_model=dict)
async def ward_metrics(db: Session = Depends(get_db)):
    """
    Public per-ward complaint metrics: total, open, resolved counts and
    resolution rate. Powers the public dashboard — no auth required, and
    no personal data is exposed.
    """
    try:
        counts = (
            db.query(
                Complaint.ward_id,
                Complaint.status,
                func.count(Complaint.id),
            )
            .group_by(Complaint.ward_id, Complaint.status)
            .all()
        )

        by_ward = {}
        for ward_id, c_status, n in counts:
            entry = by_ward.setdefault(
                str(ward_id), {"total": 0, "open": 0, "in_progress": 0, "resolved": 0}
            )
            entry["total"] += n
            value = c_status.value if hasattr(c_status, "value") else c_status
            if value in ("open", "assigned"):
                entry["open"] += n
            elif value == "in_progress":
                entry["in_progress"] += n
            elif value == "resolved":
                entry["resolved"] += n

        avg_hours_by_ward = metrics_service.get_avg_resolution_hours(db)

        wards = db.query(Ward).order_by(Ward.ward_number).all()
        result = []
        for w in wards:
            stats = by_ward.get(
                str(w.id), {"total": 0, "open": 0, "in_progress": 0, "resolved": 0}
            )
            resolution_rate = (
                round(stats["resolved"] / stats["total"] * 100, 1)
                if stats["total"]
                else None
            )
            avg_res_hours = avg_hours_by_ward.get(str(w.id))
            score = metrics_service.compute_cleanliness_score(
                total=stats["total"],
                open_count=stats["open"],
                resolved=stats["resolved"],
                avg_res_hours=avg_res_hours,
                population=w.population,
            )
            result.append(
                {
                    "ward_id": str(w.id),
                    "ward_name": w.name,
                    "ward_number": w.ward_number,
                    **stats,
                    "resolution_rate": resolution_rate,
                    "cleanliness_score": score,
                    "band": metrics_service.score_band(score),
                    "avg_resolution_hours": avg_res_hours,
                }
            )

        return {"metrics": result}
    except Exception as e:
        logger.error(f"Error computing ward metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute metrics",
        )
