"""
Before/after resolution photo verification.

Combines two signals when an officer resolves a complaint with an "after" photo:
- SSIM (structural similarity) between the original and after photo — a very
  high similarity (> 0.85) suggests the scene did not change (suspicious);
  low similarity supports a genuine cleanup. Supporting signal only.
- GPT-4o vision verdict (ai_service.verify_cleanup) — the deciding signal.

The result is persisted on the complaint's Assignment row (created on demand
for seeded/legacy complaints that never got one). All failure paths degrade
gracefully — verification never blocks resolution.
"""

import io
import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.orm import Session

from backend_models import Assignment, AssignmentStatus, Complaint

from backend.app.services import ai_service
from backend.app.utils.s3 import get_s3_client

logger = logging.getLogger(__name__)

SUSPICIOUS_SSIM_THRESHOLD = 0.85


def parse_s3_object_from_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Extract (bucket, key) from either a path-style URL
    (http://localhost:4566/<bucket>/<key>, LocalStack) or a virtual-host AWS
    URL (https://<bucket>.s3.<region>.amazonaws.com/<key>).
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        host = parsed.netloc
        if ".s3." in host or host.endswith(".amazonaws.com"):
            bucket = host.split(".")[0]
            return (bucket, path) if bucket and path else None
        parts = path.split("/", 1)
        if len(parts) == 2 and parts[0] and parts[1]:
            return (parts[0], parts[1])
        return None
    except Exception:
        return None


def download_image_bytes(url: str) -> Optional[bytes]:
    """Fetch an image from S3 by its public URL. None on any failure."""
    parsed = parse_s3_object_from_url(url)
    if not parsed:
        return None
    bucket, key = parsed
    try:
        obj = get_s3_client().get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()
    except Exception as e:
        logger.warning(f"Could not download original image {key}: {str(e)}")
        return None


def compute_ssim(before_bytes: bytes, after_bytes: bytes) -> Optional[float]:
    """SSIM between two images (grayscale, 256x256). None on any failure."""
    try:
        import numpy as np
        from PIL import Image
        from skimage.metrics import structural_similarity

        def prep(data: bytes):
            img = Image.open(io.BytesIO(data)).convert("L").resize((256, 256))
            return np.asarray(img)

        score = structural_similarity(
            prep(before_bytes), prep(after_bytes), data_range=255
        )
        return round(float(score), 3)
    except Exception as e:
        logger.warning(f"SSIM computation failed: {str(e)}")
        return None


def verify_resolution(
    db: Session,
    complaint: Complaint,
    officer_id: UUID,
    after_bytes: bytes,
    after_url: str,
    notes: Optional[str] = None,
) -> dict:
    """
    Verify a cleanup photo and persist the outcome on the Assignment row.

    Returns: {after_image_url, ssim, suspicious_similarity, ai, verified}
    """
    before_bytes = None
    if complaint.image_urls:
        before_bytes = download_image_bytes(complaint.image_urls[0])

    ssim = (
        compute_ssim(before_bytes, after_bytes) if before_bytes is not None else None
    )
    suspicious = ssim is not None and ssim > SUSPICIOUS_SSIM_THRESHOLD

    ai_verdict = ai_service.verify_cleanup(before_bytes, after_bytes)
    verified = ai_verdict["cleaned"] is True

    try:
        assignment = (
            db.query(Assignment)
            .filter(Assignment.complaint_id == complaint.id)
            .first()
        )
        if not assignment:
            # Seeded/legacy complaints may never have been auto-assigned
            assignment = Assignment(
                complaint_id=complaint.id,
                assigned_to=officer_id,
                assigned_at=datetime.utcnow(),
            )
            db.add(assignment)

        assignment.status = AssignmentStatus.completed
        assignment.completed_at = datetime.utcnow()
        assignment.completion_image_url = after_url
        assignment.verified = verified
        assignment.verification_ssim_score = ssim
        note_parts = [notes] if notes else []
        if suspicious:
            note_parts.append(
                f"Auto-flag: after photo very similar to original (SSIM {ssim})"
            )
        if ai_verdict.get("note"):
            note_parts.append(f"AI: {ai_verdict['note']}")
        assignment.notes = " | ".join(note_parts)[:500] or None
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist verification: {str(e)}")

    return {
        "after_image_url": after_url,
        "ssim": ssim,
        "suspicious_similarity": suspicious,
        "ai": ai_verdict,
        "verified": verified,
    }
