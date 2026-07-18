# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CleanLoop — a community waste & sanitation reporting platform (FastAPI + PostgreSQL/PostGIS backend, React PWA frontend). Citizens report waste with photo + GPS; officers get AI-ranked assignments; public dashboards show ward metrics. Product spec is in `PRD.md`.

## Unusual file layout (read this first)

The repo does NOT use a conventional package layout. Entry-point and shared modules live at the **repo root** with `backend_` / `frontend_` filename prefixes, while routers/services live under `backend/app/`:

- `backend_main.py` — FastAPI app entry point (registers routers from `backend/app/api/`)
- `backend_database.py` — engine, `SessionLocal`, `Base`, `get_db`
- `backend_models.py` — all SQLAlchemy models (User, Ward, Complaint, Assignment, Hotspot, WardMetric)
- `backend_schemas.py` — Pydantic schemas
- `backend/app/api/` — routers (auth, complaints, assignments), mounted under `/api`
- `backend/app/services/` — business logic (auth_service, complaint_service, ai_service, image_service, assignment_service)
- `backend/app/utils/` — s3.py, validators.py
- `backend/app/workers/celery_tasks.py` — async image classification
- `backend/app/dependencies.py` — `get_db`, `get_current_user`, `get_current_officer` (JWT bearer auth)

Imports mix both styles (`from backend_database import Base` and `from backend.app.api import auth`), so **everything must run from the repo root** — the root is the import path.

The frontend lives in `frontend/` (standard Vite structure: `src/pages/`, `src/store.ts` zustand auth store, `src/api.ts` axios client). The root-level `frontend_*` files are the historical originals the structure was assembled from — **`frontend/` is the source of truth; do not edit the root-prefixed frontend files.**

## Commands

Backend commands run from the repo root; use the venv at `venv/` (Python 3.13 — the 2023 pins in `requirements.txt` don't build on it, so packages are installed with relaxed pins).

```bash
# Infrastructure (PostgreSQL+PostGIS, Redis, LocalStack S3 on :4566)
docker-compose up -d

# Create database tables (no Alembic — plain create_all).
# PYTHONPATH=. is required: the script lives in backend/ but imports root modules.
PYTHONPATH=. ./venv/Scripts/python backend/init_db.py

# Run the API (http://localhost:8000, docs at /docs)
./venv/Scripts/python -m uvicorn backend_main:app --reload

# Seed dev data: city-wide fallback ward + 8 named Chennai wards, one officer
# each (officer@cleanloop.dev, officer.<slug>@cleanloop.dev / officer123).
# Idempotent. Required before complaint submission works — ward auto-detection
# needs a ward polygon. --demo-data also seeds a demo citizen
# (citizen@cleanloop.dev / citizen123) + ~90 complaints (3 hotspot clusters)
# for the dashboard; demo seeding is skipped if CL-DEMO- tickets exist.
PYTHONPATH=. ./venv/Scripts/python backend/seed_dev_data.py --demo-data

# Integration tests (requires the server + docker services running)
./venv/Scripts/python test_complaints_integration.py
# AI-draft flow + dashboard endpoints (needs --demo-data seed; API_URL to override port)
./venv/Scripts/python test_dashboard_integration.py
```

Frontend (Vite, port 3000, proxies `/api` → localhost:8000), run from `frontend/`: `npm run dev` / `npm run build` / `npm run lint` / `npm run type-check`.

The S3 bucket must exist before image upload works — create `cleanloop-images` via boto3 against `http://localhost:4566` after LocalStack starts.

There is no pytest suite yet; `test_complaints_integration.py` is a standalone script that hits a live server.

Copy `.env.example` to `.env` before running. LocalStack emulates S3 in dev (`AWS_ENDPOINT_URL=http://localhost:4566`).

## Architecture notes

- **Auth**: JWT bearer tokens (python-jose). Role gating via `get_current_user` / `get_current_officer` dependencies in `backend/app/dependencies.py`. User types: citizen, officer, admin.
- **Geospatial**: PostGIS via GeoAlchemy2 — `Complaint.location` and `Hotspot.centroid` are `Geometry('POINT', srid=4326)`, `Ward.geometry` is a POLYGON. Docker image is `postgis/postgis:16-3.4` (the 16-3.3 tag was removed from Docker Hub). LocalStack is pinned to `4.3` — `latest` requires a Pro auth token.
- **Models have no SQLAlchemy relationships** — foreign keys are plain UUID columns; joins are done manually in services.
- **AI pipeline**: image upload → S3 → Celery task → OpenAI Vision classification, results stored on `Complaint.ai_waste_type` / `ai_confidence`.
- **Deployment**: `.github/workflows/deploy.yml` provisions a **fresh EC2 instance in AWS** and deploys the docker-compose stack. It is manual-only (`workflow_dispatch`) — trigger it from the GitHub Actions tab. Do not change it back to `on: push` without the user's explicit request.

## Documentation files

The root contains ~25 phase/status markdown files (PHASE_*, IMPLEMENTATION_*, *_COMPLETE.md, etc.) — these are historical progress reports, not current instructions. Authoritative docs: `PRD.md` (product spec), `README.md`, `SETUP.md`.
