"""
Seed development data for CleanLoop.

Creates:
- A Chennai-wide fallback ward "Chennai Central (Dev)" (so complaint ward
  auto-detection always succeeds) + the original dev officer account.
- 8 named Chennai wards (non-overlapping rectangles over real localities),
  each with its own officer (officer.<slug>@cleanloop.dev / officer123).
- With --demo-data: a demo citizen and ~90 complaints spread over the past
  45 days, 40% of them clustered around 3 hotspot centers so DBSCAN
  hotspot detection has something to find.

Idempotent — safe to re-run. Demo complaints are skipped if any CL-DEMO-
ticket already exists.

Usage (from repo root):
    PYTHONPATH=. python backend/seed_dev_data.py [--demo-data]
"""

import argparse
import logging
import random
from datetime import datetime, timedelta

from backend_database import SessionLocal
from backend_models import (
    Assignment,
    AssignmentStatus,
    Complaint,
    ComplaintStatus,
    User,
    UserType,
    Ward,
    WasteType,
)
from backend.app.services.auth_service import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Bounding box covering greater Chennai (lon lat pairs, WKT polygon).
# Fallback ward so ward auto-detection succeeds anywhere in the city.
CHENNAI_POLYGON = (
    "POLYGON((80.10 12.85, 80.35 12.85, 80.35 13.25, 80.10 13.25, 80.10 12.85))"
)

OFFICER_EMAIL = "officer@cleanloop.dev"
OFFICER_PASSWORD = "officer123"
CITIZEN_EMAIL = "citizen@cleanloop.dev"
CITIZEN_PASSWORD = "citizen123"

# Named wards as non-overlapping rectangles over real Chennai localities.
# (name, ward_number, population, (lon_min, lat_min, lon_max, lat_max))
WARDS = [
    ("Velachery", 2, 92000, (80.210, 12.960, 80.240, 12.995)),
    ("Adyar", 3, 78000, (80.230, 12.995, 80.260, 13.020)),
    ("Besant Nagar", 4, 54000, (80.260, 12.980, 80.290, 13.010)),
    ("Mylapore", 5, 88000, (80.250, 13.020, 80.280, 13.050)),
    ("T. Nagar", 6, 110000, (80.220, 13.025, 80.250, 13.055)),
    ("Kodambakkam", 7, 96000, (80.200, 13.030, 80.220, 13.060)),
    ("Anna Nagar", 8, 105000, (80.195, 13.065, 80.230, 13.100)),
    ("Perambur", 9, 99000, (80.230, 13.095, 80.265, 13.130)),
]

# Hotspot centers (lat, lon) — inside Mylapore, T. Nagar, Velachery tiles.
HOTSPOT_CENTERS = [
    ("Marina beach edge", 13.045, 80.270, "Mylapore"),
    ("T. Nagar market corner", 13.040, 80.233, "T. Nagar"),
    ("Velachery lake edge", 12.978, 80.222, "Velachery"),
]

DEMO_COMPLAINT_COUNT = 90
DEMO_TICKET_PREFIX = "CL-DEMO-"

DESCRIPTIONS = {
    WasteType.bin: "Overflowing public bin with waste spilling onto the pavement.",
    WasteType.dumping: "Illegal dumping of mixed household waste on the roadside.",
    WasteType.construction: "Construction debris left blocking part of the street.",
    WasteType.biohazard: "Decaying organic waste creating a sanitation hazard.",
}


def bbox_to_wkt(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    return (
        f"POLYGON(({lon_min} {lat_min}, {lon_max} {lat_min}, "
        f"{lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))"
    )


def slugify(name):
    return name.lower().replace(".", "").replace(" ", "")


def ensure_officer(db, email, ward_id):
    officer = db.query(User).filter(User.email == email).first()
    if not officer:
        officer = User(
            email=email,
            password_hash=hash_password(OFFICER_PASSWORD),
            user_type=UserType.officer,
            ward_id=ward_id,
            is_active=True,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)
        logger.info(f"Created officer: {email} / {OFFICER_PASSWORD}")
    elif officer.ward_id != ward_id:
        officer.ward_id = ward_id
        db.commit()
    return officer


def seed_wards_and_officers(db):
    # Fallback city-wide dev ward + original officer
    dev_ward = db.query(Ward).filter(Ward.name == "Chennai Central (Dev)").first()
    if not dev_ward:
        dev_ward = Ward(
            name="Chennai Central (Dev)",
            ward_number=1,
            geometry=CHENNAI_POLYGON,
            population=100000,
        )
        db.add(dev_ward)
        db.commit()
        db.refresh(dev_ward)
        logger.info(f"Created ward: {dev_ward.name} ({dev_ward.id})")
    else:
        logger.info(f"Ward already exists: {dev_ward.name}")

    officer = ensure_officer(db, OFFICER_EMAIL, dev_ward.id)
    dev_ward.primary_officer_id = officer.id
    db.commit()

    # Named locality wards, one officer each
    ward_by_name = {}
    for name, number, population, bbox in WARDS:
        ward = db.query(Ward).filter(Ward.name == name).first()
        if not ward:
            ward = Ward(
                name=name,
                ward_number=number,
                geometry=bbox_to_wkt(bbox),
                population=population,
            )
            db.add(ward)
            db.commit()
            db.refresh(ward)
            logger.info(f"Created ward: {name} ({ward.id})")
        else:
            logger.info(f"Ward already exists: {name}")
        w_officer = ensure_officer(db, f"officer.{slugify(name)}@cleanloop.dev", ward.id)
        if ward.primary_officer_id != w_officer.id:
            ward.primary_officer_id = w_officer.id
            db.commit()
        ward_by_name[name] = (ward, bbox)

    # Give the fallback dev ward a small slice of scattered complaints too,
    # so officer@cleanloop.dev has something to see in the demo.
    ward_by_name[dev_ward.name] = (dev_ward, (80.10, 12.85, 80.35, 13.25))
    return ward_by_name


def ensure_citizen(db):
    citizen = db.query(User).filter(User.email == CITIZEN_EMAIL).first()
    if not citizen:
        citizen = User(
            email=CITIZEN_EMAIL,
            password_hash=hash_password(CITIZEN_PASSWORD),
            user_type=UserType.citizen,
            is_active=True,
        )
        db.add(citizen)
        db.commit()
        db.refresh(citizen)
        logger.info(f"Created citizen: {CITIZEN_EMAIL} / {CITIZEN_PASSWORD}")
    return citizen


def seed_demo_complaints(db, ward_by_name):
    existing = (
        db.query(Complaint)
        .filter(Complaint.ticket_number.like(f"{DEMO_TICKET_PREFIX}%"))
        .first()
    )
    if existing:
        logger.info("Demo complaints already seeded — skipping.")
        return

    citizen = ensure_citizen(db)
    rng = random.Random(42)
    now = datetime.utcnow()

    statuses = (
        [ComplaintStatus.resolved] * 35
        + [ComplaintStatus.open] * 25
        + [ComplaintStatus.assigned] * 20
        + [ComplaintStatus.in_progress] * 20
    )
    waste_types = list(WasteType)

    created = 0
    for i in range(DEMO_COMPLAINT_COUNT):
        if i % 5 < 2:
            # 40%: clustered around a hotspot center (sigma ~0.0008 deg ≈ 90m,
            # tight enough for DBSCAN eps=250m to find them after status/time filters)
            _, c_lat, c_lon, ward_name = HOTSPOT_CENTERS[i % len(HOTSPOT_CENTERS)]
            lat = rng.gauss(c_lat, 0.0008)
            lon = rng.gauss(c_lon, 0.0008)
            ward, _ = ward_by_name[ward_name]
            severity = rng.choice([3, 4, 4, 5])
        else:
            # 60%: scattered uniformly inside a random named ward
            name = rng.choice(list(ward_by_name.keys()))
            ward, bbox = ward_by_name[name]
            lon_min, lat_min, lon_max, lat_max = bbox
            lat = rng.uniform(lat_min + 0.002, lat_max - 0.002)
            lon = rng.uniform(lon_min + 0.002, lon_max - 0.002)
            severity = rng.choice([1, 2, 2, 3, 3, 4])

        status = rng.choice(statuses)
        waste_type = rng.choice(waste_types)
        created_at = now - timedelta(
            days=rng.uniform(0, 45), hours=rng.uniform(0, 24)
        )
        resolved_at = None
        if status == ComplaintStatus.resolved:
            resolved_at = created_at + timedelta(hours=rng.uniform(4, 96))

        complaint = Complaint(
            ticket_number=f"{DEMO_TICKET_PREFIX}{i + 1:04d}",
            citizen_id=citizen.id,
            ward_id=ward.id,
            location=f"POINT({lon} {lat})",
            description=DESCRIPTIONS[waste_type],
            waste_type=waste_type,
            severity_score=severity,
            image_urls=[],
            status=status,
            created_at=created_at,
            updated_at=created_at,
            resolved_at=resolved_at,
            ai_waste_type=waste_type.value if rng.random() < 0.7 else None,
            ai_confidence=round(rng.uniform(0.55, 0.98), 2),
        )
        db.add(complaint)
        created += 1

    db.commit()
    logger.info(f"Seeded {created} demo complaints across {len(ward_by_name)} wards.")


def ensure_demo_assignments(db):
    """
    Create Assignment rows for demo complaints that were inserted directly
    (bypassing auto-assign), so officer queues, status timelines and
    verification badges have data. Idempotent; also upgrades existing DBs.
    """
    rng = random.Random(7)
    demo_complaints = (
        db.query(Complaint)
        .filter(
            Complaint.ticket_number.like(f"{DEMO_TICKET_PREFIX}%"),
            Complaint.status.in_(
                [
                    ComplaintStatus.assigned,
                    ComplaintStatus.in_progress,
                    ComplaintStatus.resolved,
                ]
            ),
        )
        .all()
    )
    if not demo_complaints:
        return

    existing = {
        str(a.complaint_id)
        for a in db.query(Assignment)
        .filter(Assignment.complaint_id.in_([c.id for c in demo_complaints]))
        .all()
    }
    officer_by_ward = {
        str(w.id): w.primary_officer_id
        for w in db.query(Ward).all()
        if w.primary_officer_id
    }

    created = 0
    for c in demo_complaints:
        if str(c.id) in existing:
            continue
        officer_id = officer_by_ward.get(str(c.ward_id))
        if not officer_id:
            continue
        assigned_at = c.created_at + timedelta(hours=rng.uniform(1, 6))
        assignment = Assignment(
            complaint_id=c.id,
            assigned_to=officer_id,
            assigned_at=assigned_at,
            due_at=assigned_at + timedelta(hours=24),
        )
        if c.status == ComplaintStatus.resolved:
            assignment.status = AssignmentStatus.completed
            assignment.completed_at = c.resolved_at
            if rng.random() < 0.6:
                assignment.verified = True
                assignment.verification_ssim_score = round(rng.uniform(0.20, 0.60), 2)
        elif c.status == ComplaintStatus.in_progress:
            assignment.status = AssignmentStatus.in_progress
        db.add(assignment)
        created += 1

    db.commit()
    logger.info(f"Seeded {created} demo assignments.")


def seed(demo_data: bool = False):
    db = SessionLocal()
    try:
        ward_by_name = seed_wards_and_officers(db)
        if demo_data:
            seed_demo_complaints(db, ward_by_name)
            ensure_demo_assignments(db)
        logger.info("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed CleanLoop dev data")
    parser.add_argument(
        "--demo-data",
        action="store_true",
        help="Also seed ~90 demo complaints for the dashboard/hotspot demo",
    )
    args = parser.parse_args()
    seed(demo_data=args.demo_data)
