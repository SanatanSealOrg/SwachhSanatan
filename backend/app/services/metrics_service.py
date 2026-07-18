"""
Ward cleanliness scoring and hotspot detection for CleanLoop.

Cleanliness score (0-100, explainable):
    score = 100
          - 45 * open complaint density (open/population*10000, capped at 1)
          - 25 * (1 - resolution rate)
          - 30 * avg resolution time penalty (avg_hours/168, capped at 1)

Hotspots: DBSCAN clustering (haversine metric, eps=250m, min_samples=4) over
active complaints from the last 30 days, with a pure-Python grid fallback if
scikit-learn is unavailable. Results are cached in-process for 60 seconds.
"""

import logging
import math
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend_models import Complaint, ComplaintStatus

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6371000.0
HOTSPOT_EPS_M = 250.0
HOTSPOT_MIN_SAMPLES = 4
HOTSPOT_WINDOW_DAYS = 30
HOTSPOT_MIN_RADIUS_M = 60.0
_CACHE_TTL_S = 60.0

_hotspot_cache: dict = {"computed_at": 0.0, "result": None}


def compute_cleanliness_score(
    total: int,
    open_count: int,
    resolved: int,
    avg_res_hours: Optional[float],
    population: Optional[int],
) -> float:
    """Score a ward 0-100. A ward with zero complaints scores 100."""
    if total == 0:
        return 100.0
    resolution_rate = resolved / total
    if population and population > 0:
        density = min(open_count / population * 10000, 1.0)
    else:
        density = min(open_count / 20, 1.0)
    time_penalty = min((avg_res_hours or 0.0) / 168.0, 1.0)
    score = 100 - 45 * density - 25 * (1 - resolution_rate) - 30 * time_penalty
    return round(max(0.0, min(100.0, score)), 1)


def score_band(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"


def get_avg_resolution_hours(db: Session) -> Dict[str, float]:
    """Average resolution time in hours per ward (resolved complaints only)."""
    rows = (
        db.query(
            Complaint.ward_id,
            func.avg(
                func.extract("epoch", Complaint.resolved_at - Complaint.created_at)
                / 3600.0
            ),
        )
        .filter(Complaint.resolved_at.isnot(None))
        .group_by(Complaint.ward_id)
        .all()
    )
    return {str(ward_id): round(float(hours), 1) for ward_id, hours in rows if hours}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _cluster_labels(points: List[tuple]) -> List[int]:
    """Cluster (lat, lon) points; returns a label per point (-1 = noise)."""
    try:
        import numpy as np
        from sklearn.cluster import DBSCAN

        coords = np.radians(np.array(points))
        labels = (
            DBSCAN(
                eps=HOTSPOT_EPS_M / EARTH_RADIUS_M,
                min_samples=HOTSPOT_MIN_SAMPLES,
                metric="haversine",
            )
            .fit(coords)
            .labels_
        )
        return labels.tolist()
    except ImportError:
        # Grid fallback: bucket into ~250m cells, cells with enough points
        # form clusters (coarser than DBSCAN but adequate for the demo)
        logger.warning("scikit-learn unavailable — using grid clustering fallback")
        cell = HOTSPOT_EPS_M / 111320.0  # degrees latitude per eps
        buckets: Dict[tuple, List[int]] = {}
        for idx, (lat, lon) in enumerate(points):
            key = (int(lat / cell), int(lon / cell))
            buckets.setdefault(key, []).append(idx)
        labels = [-1] * len(points)
        next_label = 0
        for members in buckets.values():
            if len(members) >= HOTSPOT_MIN_SAMPLES:
                for idx in members:
                    labels[idx] = next_label
                next_label += 1
        return labels


def compute_hotspots(db: Session) -> dict:
    """Detect active waste hotspots (cached for 60s)."""
    now = time.monotonic()
    if (
        _hotspot_cache["result"] is not None
        and now - _hotspot_cache["computed_at"] < _CACHE_TTL_S
    ):
        return _hotspot_cache["result"]

    cutoff = datetime.utcnow() - timedelta(days=HOTSPOT_WINDOW_DAYS)
    rows = (
        db.query(
            func.ST_Y(Complaint.location).label("lat"),
            func.ST_X(Complaint.location).label("lon"),
            Complaint.waste_type,
            Complaint.severity_score,
            Complaint.created_at,
        )
        .filter(
            Complaint.created_at >= cutoff,
            Complaint.status.in_(
                [
                    ComplaintStatus.open,
                    ComplaintStatus.assigned,
                    ComplaintStatus.in_progress,
                ]
            ),
        )
        .all()
    )

    hotspots = []
    algorithm = "dbscan"
    if len(rows) >= HOTSPOT_MIN_SAMPLES:
        points = [(r.lat, r.lon) for r in rows]
        labels = _cluster_labels(points)
        clusters: Dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            if label >= 0:
                clusters.setdefault(label, []).append(idx)

        for label, members in sorted(clusters.items()):
            lats = [rows[i].lat for i in members]
            lons = [rows[i].lon for i in members]
            c_lat = sum(lats) / len(lats)
            c_lon = sum(lons) / len(lons)
            radius = max(
                max(_haversine_m(c_lat, c_lon, rows[i].lat, rows[i].lon) for i in members),
                HOTSPOT_MIN_RADIUS_M,
            )
            waste_counts = Counter(
                (
                    rows[i].waste_type.value
                    if hasattr(rows[i].waste_type, "value")
                    else rows[i].waste_type
                )
                for i in members
                if rows[i].waste_type
            )
            newest = max(rows[i].created_at for i in members if rows[i].created_at)
            hotspots.append(
                {
                    "id": label,
                    "centroid": {"lat": round(c_lat, 6), "lon": round(c_lon, 6)},
                    "radius_m": round(radius, 1),
                    "count": len(members),
                    "dominant_waste_type": (
                        waste_counts.most_common(1)[0][0] if waste_counts else None
                    ),
                    "avg_severity": round(
                        sum(rows[i].severity_score for i in members) / len(members), 1
                    ),
                    "last_reported": newest.isoformat() if newest else None,
                }
            )
        hotspots.sort(key=lambda h: h["count"], reverse=True)

    result = {
        "hotspots": hotspots,
        "computed_at": datetime.utcnow().isoformat(),
        "algorithm": algorithm,
        "window_days": HOTSPOT_WINDOW_DAYS,
    }
    _hotspot_cache["computed_at"] = now
    _hotspot_cache["result"] = result
    logger.info(f"Hotspots computed: {len(hotspots)} clusters from {len(rows)} points")
    return result
