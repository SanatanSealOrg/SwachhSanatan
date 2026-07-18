#!/usr/bin/env python3
"""
Integration tests for Round 2: AI wizard ward-mapping, officer priority queue,
chronic hotspots, before/after resolution verification, My Complaints and the
public ticket tracker.

Usage (server + docker services running, demo data seeded):
    PYTHONPATH=. python backend/seed_dev_data.py --demo-data
    python test_round2_integration.py

Env: API_URL (default http://localhost:8000)
"""

import io
import os
import sys

import requests

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

CITIZEN = {"email": "citizen@cleanloop.dev", "password": "citizen123"}
TNAGAR_OFFICER = {"email": "officer.tnagar@cleanloop.dev", "password": "officer123"}

results = []


def check(name, passed, message=""):
    passed = bool(passed)
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}" + (f"  → {message}" if message else ""))
    results.append(passed)


def section(title):
    print(f"\n{YELLOW}{'=' * 60}\n{title.center(60)}\n{'=' * 60}{RESET}")


def make_jpeg(color):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (640, 480), color).save(buf, format="JPEG")
    return buf.getvalue()


def main():
    section("Logins")
    r = requests.post(f"{BASE_URL}/api/auth/login", json=CITIZEN)
    check("Citizen login", r.status_code == 200,
          "run: PYTHONPATH=. python backend/seed_dev_data.py --demo-data" if r.status_code != 200 else "")
    if r.status_code != 200:
        sys.exit(1)
    citizen = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = requests.post(f"{BASE_URL}/api/auth/login", json=TNAGAR_OFFICER)
    check("T. Nagar officer login", r.status_code == 200)
    officer = {"Authorization": f"Bearer {r.json()['access_token']}"}
    tnagar_ward_id = requests.get(
        f"{BASE_URL}/api/auth/me", headers=officer
    ).json()["ward_id"]

    section("A1 — AI wizard ward mapping")
    jpeg = make_jpeg((120, 90, 60))
    r = requests.post(
        f"{BASE_URL}/api/complaints/analyze",
        headers=citizen,
        files={"file": ("trash.jpg", jpeg, "image/jpeg")},
        data={"latitude": 13.040, "longitude": 80.233},
    )
    body = r.json()
    ward = body.get("ward")
    check("Analyze with T. Nagar coords returns ward block",
          r.status_code == 200 and ward is not None)
    check("Ward mapped to T. Nagar with officer_available",
          bool(ward) and ward.get("name") == "T. Nagar"
          and isinstance(ward.get("officer_available"), bool),
          f"ward={ward.get('name') if ward else None}")
    image_key = body["image"]["key"]

    r = requests.post(
        f"{BASE_URL}/api/complaints/analyze",
        headers=citizen,
        files={"file": ("trash.jpg", jpeg, "image/jpeg")},
    )
    check("Analyze without coords → ward null",
          r.status_code == 200 and r.json().get("ward") is None)

    section("B3/B5 — Priority queue + aging")
    r = requests.get(
        f"{BASE_URL}/api/complaints/queue?ward_id={tnagar_ward_id}", headers=officer
    )
    q = r.json()
    queue = q.get("queue", [])
    check("Queue returns items", r.status_code == 200 and len(queue) > 0,
          f"{len(queue)} items")
    scores = [i["priority_score"] for i in queue]
    check("Queue sorted by priority desc", scores == sorted(scores, reverse=True))
    check(
        "Items carry band/reasons/bucket/coords",
        all(
            i["priority_band"] in ("critical", "high", "medium", "low")
            and isinstance(i["reasons"], list) and i["reasons"]
            and i["age_bucket"] in ("fresh", "aging", "overdue")
            and isinstance(i["lat"], float) and isinstance(i["lon"], float)
            for i in queue
        ),
    )
    c = q["counts"]
    check("Aging counts sum to total",
          c["fresh"] + c["aging"] + c["overdue"] == c["total"] == len(queue),
          str(c))
    check("At least one overdue item (45-day seed)", c["overdue"] >= 1)
    check("resolved_total present", isinstance(q.get("resolved_total"), int))

    other_ward = requests.get(f"{BASE_URL}/api/wards").json()["wards"]
    other_id = next(w["id"] for w in other_ward if w["id"] != tnagar_ward_id)
    r = requests.get(f"{BASE_URL}/api/complaints/queue?ward_id={other_id}", headers=officer)
    check("Queue for other ward → 403", r.status_code == 403)
    r = requests.get(
        f"{BASE_URL}/api/complaints/queue?ward_id={tnagar_ward_id}", headers=citizen
    )
    check("Queue with citizen token → 401/403", r.status_code in (401, 403))

    section("B4 — Chronic hotspots + ward filter")
    all_h = requests.get(f"{BASE_URL}/api/hotspots").json()["hotspots"]
    check("Hotspots carry chronic + first_reported",
          all("chronic" in h and "first_reported" in h and "ward_id" in h for h in all_h))
    check("≥1 chronic hotspot overall", any(h["chronic"] for h in all_h),
          f"{sum(1 for h in all_h if h['chronic'])} chronic of {len(all_h)}")
    filt = requests.get(
        f"{BASE_URL}/api/hotspots?ward_id={tnagar_ward_id}"
    ).json()["hotspots"]
    check("Ward filter returns subset",
          len(filt) <= len(all_h)
          and all(h["ward_id"] == tnagar_ward_id for h in filt))

    section("B6 — Resolve with verification")
    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=citizen,
        data={
            "description": "Round2 verification test — pile of waste",
            "latitude": 13.041, "longitude": 80.235,
            "waste_type": "dumping", "severity_score": 4,
            "image_key": image_key, "ai_waste_type": "dumping", "ai_confidence": 0.9,
        },
    )
    check("Create complaint (image_key flow)", r.status_code == 201)
    complaint = r.json()
    cid = complaint["id"]

    r = requests.patch(
        f"{BASE_URL}/api/complaints/{cid}", headers=officer,
        json={"status": "in_progress"},
    )
    check("Officer starts complaint (legacy PATCH)", r.status_code == 200)

    r = requests.post(
        f"{BASE_URL}/api/complaints/{cid}/resolve",
        headers=officer,
        files={"file": ("after.jpg", make_jpeg((200, 200, 200)), "image/jpeg")},
        data={"notes": "Cleaned by crew"},
    )
    body = r.json()
    v = body.get("verification")
    check("Resolve with after photo → 200 + resolved",
          r.status_code == 200 and body["complaint"]["status"] == "resolved")
    check(
        "Verification block complete",
        bool(v)
        and "after_image_url" in v
        and (v["ssim"] is None or isinstance(v["ssim"], float))
        and v["ai"]["source"] in ("openai", "mock")
        and isinstance(v["verified"], bool),
        f"ssim={v.get('ssim') if v else None} ai={v['ai']['source'] if v else None} verified={v.get('verified') if v else None}",
    )
    check("resolved_total returned", isinstance(body.get("resolved_total"), int))

    r = requests.post(f"{BASE_URL}/api/complaints/{cid}/resolve", headers=officer)
    check("Re-resolving → 400", r.status_code == 400)

    # resolve-without-photo path
    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=citizen,
        files={"file": ("x.jpg", make_jpeg((90, 120, 60)), "image/jpeg")},
        data={"description": "Round2 no-photo resolve", "latitude": 13.042,
              "longitude": 80.234, "waste_type": "bin", "severity_score": 2},
    )
    cid2 = r.json()["id"]
    r = requests.post(f"{BASE_URL}/api/complaints/{cid2}/resolve", headers=officer)
    check("Resolve without photo → 200, verification null",
          r.status_code == 200 and r.json()["verification"] is None
          and r.json()["complaint"]["status"] == "resolved")

    section("C8 — My Complaints")
    r = requests.get(f"{BASE_URL}/api/complaints/mine", headers=citizen)
    mine = r.json().get("complaints", [])
    check("Mine returns complaints", r.status_code == 200 and len(mine) > 0,
          f"{len(mine)} items")
    target = next((m for m in mine if m["id"] == cid), None)
    check(
        "Resolved item carries assignment + ward_name",
        bool(target)
        and target.get("ward_name")
        and target.get("assignment")
        and target["assignment"]["completion_image_url"]
        and isinstance(target["assignment"]["verified"], bool),
    )

    section("City-wide desk (Dev ward)")
    wards = requests.get(f"{BASE_URL}/api/wards").json()["wards"]
    dev_ward_id = next(w["id"] for w in wards if "(Dev)" in w["name"])

    without_dev = requests.get(f"{BASE_URL}/api/wards/geojson").json()["features"]
    with_dev = requests.get(
        f"{BASE_URL}/api/wards/geojson?include_dev=true"
    ).json()["features"]
    check("geojson include_dev adds the desk ward",
          len(with_dev) == len(without_dev) + 1,
          f"{len(without_dev)} → {len(with_dev)}")

    dev_hotspots = requests.get(
        f"{BASE_URL}/api/hotspots?ward_id={dev_ward_id}"
    ).json()["hotspots"]
    check("City-wide ward sees ALL hotspots (containment)",
          len(dev_hotspots) == len(all_h) and len(dev_hotspots) >= 1,
          f"{len(dev_hotspots)} of {len(all_h)}")

    # Just north of the Chennai bbox (lat > 13.25): outside every ward polygon
    # but close enough not to distort demo maps.
    OUT_LAT, OUT_LON = 13.28, 80.20
    r = requests.post(
        f"{BASE_URL}/api/complaints/analyze",
        headers=citizen,
        files={"file": ("trash.jpg", jpeg, "image/jpeg")},
        data={"latitude": OUT_LAT, "longitude": OUT_LON},
    )
    w = r.json().get("ward")
    check("Analyze at out-of-city GPS maps to the desk ward",
          r.status_code == 200 and bool(w) and "(Dev)" in w["name"],
          f"ward={w.get('name') if w else None}")

    r = requests.post(
        f"{BASE_URL}/api/complaints",
        headers=citizen,
        files={"file": ("far.jpg", make_jpeg((80, 80, 140)), "image/jpeg")},
        data={"description": "Out-of-city fallback test", "latitude": OUT_LAT,
              "longitude": OUT_LON, "waste_type": "dumping", "severity_score": 3},
    )
    check("Out-of-city complaint routed to desk ward (201)",
          r.status_code == 201 and r.json()["ward_id"] == dev_ward_id)

    section("C9 — Public tracker")
    ticket = complaint["ticket_number"]
    r = requests.get(f"{BASE_URL}/api/complaints/track/{ticket}")
    t = r.json()
    check("Track without auth → 200", r.status_code == 200)
    check("Track sanitized (no citizen_id/description)",
          "citizen_id" not in t and "description" not in t)
    check(
        "Track has ward, timeline(4), verified flag, photos",
        t.get("ward", {}).get("name")
        and len(t.get("timeline", [])) == 4
        and all(s["reached"] for s in t["timeline"])
        and isinstance(t.get("verified"), bool)
        and t.get("photo_url") and t.get("after_photo_url"),
    )
    r = requests.get(f"{BASE_URL}/api/complaints/track/CL-DOES-NOT-EXIST")
    check("Unknown ticket → 404", r.status_code == 404)

    section("Summary")
    passed, total = sum(results), len(results)
    color = GREEN if passed == total else RED
    print(f"{color}{passed}/{total} tests passed{RESET}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
