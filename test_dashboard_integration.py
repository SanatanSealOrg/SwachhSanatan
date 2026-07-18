#!/usr/bin/env python3
"""
Integration tests for the AI-draft complaint flow and live dashboard endpoints.

Covers:
- POST /api/complaints/analyze (AI draft, staged image)
- POST /api/complaints with image_key reuse (no re-upload)
- GET /api/metrics/wards (cleanliness_score + band)
- GET /api/wards/geojson (FeatureCollection)
- GET /api/hotspots (DBSCAN clusters near seeded centers)
- GET /api/complaints/map (public map feed inside Chennai bbox)

Usage (server + docker services running, demo data seeded):
    PYTHONPATH=. python backend/seed_dev_data.py --demo-data
    python test_dashboard_integration.py

Env: API_URL (default http://localhost:8000)
"""

import io
import math
import os
import sys

import requests

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

CITIZEN = {"email": "citizen@cleanloop.dev", "password": "citizen123"}

# Hotspot centers seeded by backend/seed_dev_data.py --demo-data
SEEDED_HOTSPOT_CENTERS = [(13.045, 80.270), (13.040, 80.233), (12.978, 80.222)]

results = []


def check(name, passed, message=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}" + (f"  → {message}" if message else ""))
    results.append(passed)


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


def make_test_jpeg():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (120, 90, 60)).save(buf, format="JPEG")
    return buf.getvalue()


def section(title):
    print(f"\n{YELLOW}{'=' * 60}\n{title.center(60)}\n{'=' * 60}{RESET}")


def main():
    section("AI-draft complaint flow")
    r = requests.post(f"{BASE_URL}/api/auth/login", json=CITIZEN)
    check("Demo citizen login", r.status_code == 200,
          "run: PYTHONPATH=. python backend/seed_dev_data.py --demo-data" if r.status_code != 200 else "")
    if r.status_code != 200:
        sys.exit(1)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    jpeg = make_test_jpeg()
    r = requests.post(
        f"{BASE_URL}/api/complaints/analyze",
        headers=headers,
        files={"file": ("trash.jpg", jpeg, "image/jpeg")},
        data={"latitude": 13.041, "longitude": 80.235},
    )
    check("POST /complaints/analyze returns 200", r.status_code == 200)
    body = r.json()
    draft = body.get("draft", {})
    check(
        "Draft has valid fields",
        draft.get("waste_type") in (None, "bin", "dumping", "construction", "biohazard")
        and 1 <= draft.get("severity", 0) <= 5
        and 0 <= draft.get("confidence", -1) <= 1
        and bool(draft.get("description"))
        and draft.get("source") in ("openai", "mock"),
        f"source={draft.get('source')} waste_type={draft.get('waste_type')}",
    )
    image = body.get("image", {})
    check(
        "Staged image key returned",
        image.get("key", "").startswith("complaints/drafts/") and bool(image.get("url")),
    )

    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=headers,
        data={
            "description": f"{draft.get('title', 'Test')} — {draft.get('description', '')}",
            "latitude": 13.041,
            "longitude": 80.235,
            "waste_type": draft.get("waste_type") or "dumping",
            "severity_score": draft.get("severity", 3),
            "image_key": image.get("key"),
            "ai_waste_type": draft.get("waste_type") or "",
            "ai_confidence": draft.get("confidence", 0),
        },
    )
    check("Create with image_key (no file) returns 201", r.status_code == 201)
    created = r.json()
    check(
        "Complaint has promoted image + AI metadata",
        bool(created.get("image_urls"))
        and "/drafts/" not in created["image_urls"][0]
        and created.get("ai_confidence") is not None,
        created.get("ticket_number", ""),
    )

    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=headers,
        data={"description": "x", "latitude": 13.04, "longitude": 80.23,
              "image_key": "complaints/other/evil.jpg"},
    )
    check("Non-draft image_key rejected (400)", r.status_code == 400)
    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=headers,
        data={"description": "x", "latitude": 13.04, "longitude": 80.23},
    )
    check("Missing file AND image_key rejected (400)", r.status_code == 400)

    section("Dashboard endpoints")
    r = requests.get(f"{BASE_URL}/api/metrics/wards")
    metrics = r.json().get("metrics", [])
    check("GET /metrics/wards returns wards", r.status_code == 200 and len(metrics) >= 6)
    check(
        "Metrics include cleanliness_score + band",
        all(
            0 <= m.get("cleanliness_score", -1) <= 100
            and m.get("band") in ("green", "yellow", "red")
            for m in metrics
        ),
    )

    r = requests.get(f"{BASE_URL}/api/wards/geojson")
    gj = r.json()
    check(
        "GET /wards/geojson is a FeatureCollection with ≥6 features",
        r.status_code == 200
        and gj.get("type") == "FeatureCollection"
        and len(gj.get("features", [])) >= 6,
        f"{len(gj.get('features', []))} features",
    )
    check(
        "GeoJSON features carry id/name properties",
        all(f["properties"].get("id") and f["properties"].get("name") for f in gj["features"]),
    )

    r = requests.get(f"{BASE_URL}/api/hotspots")
    hotspots = r.json().get("hotspots", [])
    check("GET /hotspots returns ≥1 cluster", r.status_code == 200 and len(hotspots) >= 1,
          f"{len(hotspots)} hotspots ({r.json().get('algorithm')})")
    near_seeded = any(
        haversine_m(h["centroid"]["lat"], h["centroid"]["lon"], lat, lon) < 500
        for h in hotspots
        for lat, lon in SEEDED_HOTSPOT_CENTERS
    )
    check("A hotspot centroid lies within 500m of a seeded center", near_seeded)

    r = requests.get(f"{BASE_URL}/api/complaints/map")
    points = r.json().get("complaints", [])
    check("GET /complaints/map returns points", r.status_code == 200 and len(points) > 0,
          f"{len(points)} points")
    check(
        "All map points inside Chennai bbox",
        all(12.85 < p["lat"] < 13.25 and 80.10 < p["lon"] < 80.35 for p in points),
    )

    section("Summary")
    passed, total = sum(results), len(results)
    color = GREEN if passed == total else RED
    print(f"{color}{passed}/{total} tests passed{RESET}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
