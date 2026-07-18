"""
AI-ranked complaint priority queue for officers.

priority_score (0-100) =
    55 * severity/5                  # severity dominates
  + 15 * min(age_days/7, 1)        # capped at a week
  + 15 * in_hotspot
  + 10 * is_biohazard
  +  5 * ai_confidence (0.5 default)

Bands: critical >= 75, high >= 55, medium >= 35, low otherwise.
Age buckets: fresh < 2 days, aging 2-7 days, overdue > 7 days.
"""

import logging
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend_models import Assignment, Complaint, ComplaintStatus

from backend.app.services import metrics_service

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = [
    ComplaintStatus.open,
    ComplaintStatus.assigned,
    ComplaintStatus.in_progress,
]

WASTE_LABELS = {
    "bin": "Overflowing bin",
    "dumping": "Illegal dumping",
    "construction": "Construction debris",
    "biohazard": "Biohazard waste",
}


def priority_band(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def age_bucket(age_days: float) -> str:
    if age_days < 2:
        return "fresh"
    if age_days <= 7:
        return "aging"
    return "overdue"


def _find_hotspot(lat: float, lon: float, hotspots: List[dict]):
    for h in hotspots:
        d = metrics_service._haversine_m(
            lat, lon, h["centroid"]["lat"], h["centroid"]["lon"]
        )
        if d <= h["radius_m"]:
            return h
    return None


def build_queue(db: Session, ward_id: UUID) -> dict:
    """AI-ranked queue of active complaints in a ward, with aging counts."""
    now = datetime.utcnow()
    hotspots = metrics_service.compute_hotspots(db)["hotspots"]

    rows = (
        db.query(
            Complaint,
            func.ST_Y(Complaint.location).label("lat"),
            func.ST_X(Complaint.location).label("lon"),
        )
        .filter(
            Complaint.ward_id == ward_id,
            Complaint.status.in_(ACTIVE_STATUSES),
        )
        .all()
    )

    complaint_ids = [c.id for c, _, _ in rows]
    assignments: Dict[str, Assignment] = {}
    if complaint_ids:
        for a in (
            db.query(Assignment)
            .filter(Assignment.complaint_id.in_(complaint_ids))
            .all()
        ):
            assignments[str(a.complaint_id)] = a

    items = []
    counts = {"fresh": 0, "aging": 0, "overdue": 0, "total": 0}
    for complaint, lat, lon in rows:
        severity = complaint.severity_score or 3
        age_days = max((now - complaint.created_at).total_seconds() / 86400, 0)
        waste_type = (
            complaint.waste_type.value
            if hasattr(complaint.waste_type, "value")
            else complaint.waste_type
        )
        effective_type = waste_type or complaint.ai_waste_type
        hotspot = _find_hotspot(lat, lon, hotspots)
        confidence = (
            complaint.ai_confidence if complaint.ai_confidence is not None else 0.5
        )

        score = (
            55 * severity / 5
            + 15 * min(age_days / 7, 1.0)
            + 15 * (1 if hotspot else 0)
            + 10 * (1 if effective_type == "biohazard" else 0)
            + 5 * confidence
        )
        score = round(score, 1)
        bucket = age_bucket(age_days)
        counts[bucket] += 1
        counts["total"] += 1

        reasons = [f"Severity {severity}/5"]
        if hotspot:
            zone = "chronic zone" if hotspot.get("chronic") else "active hotspot"
            reasons.append(f"In {zone} ({hotspot['count']} reports)")
        if bucket == "overdue":
            reasons.append(f"Open for {int(age_days)} days — overdue")
        elif bucket == "aging":
            reasons.append(f"Open for {int(age_days)} days")
        if effective_type == "biohazard":
            reasons.append("Biohazard waste")

        assignment = assignments.get(str(complaint.id))
        items.append(
            {
                "id": str(complaint.id),
                "ticket_number": complaint.ticket_number,
                "status": (
                    complaint.status.value
                    if hasattr(complaint.status, "value")
                    else complaint.status
                ),
                "description": complaint.description,
                "waste_type": waste_type,
                "severity_score": complaint.severity_score,
                "image_urls": complaint.image_urls or [],
                "ai_waste_type": complaint.ai_waste_type,
                "ai_confidence": complaint.ai_confidence,
                "created_at": (
                    complaint.created_at.isoformat() if complaint.created_at else None
                ),
                "lat": lat,
                "lon": lon,
                "priority_score": score,
                "priority_band": priority_band(score),
                "reasons": reasons,
                "age_days": round(age_days, 1),
                "age_bucket": bucket,
                "in_hotspot": hotspot is not None,
                "assignment": (
                    {
                        "assigned_at": (
                            assignment.assigned_at.isoformat()
                            if assignment.assigned_at
                            else None
                        ),
                        "status": (
                            assignment.status.value
                            if hasattr(assignment.status, "value")
                            else assignment.status
                        ),
                    }
                    if assignment
                    else None
                ),
            }
        )

    items.sort(key=lambda x: x["priority_score"], reverse=True)

    resolved_total = (
        db.query(Complaint)
        .filter(
            Complaint.ward_id == ward_id,
            Complaint.status == ComplaintStatus.resolved,
        )
        .count()
    )

    return {
        "queue": items,
        "counts": counts,
        "resolved_total": resolved_total,
        "computed_at": now.isoformat(),
    }
