# CleanLoop Project Structure

## Directory Organization

```
cleanloop/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── database.py             # PostgreSQL + PostGIS connection
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── dependencies.py         # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Auth routes (login, register)
│   │   │   ├── complaints.py       # Complaint routes (CRUD, search)
│   │   │   ├── assignments.py      # Assignment routes (officer tasks)
│   │   │   ├── hotspots.py         # Hotspot detection & listing
│   │   │   └── metrics.py          # Ward metrics & dashboard
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # JWT & password handling
│   │   │   ├── image_service.py    # Image upload, compression, EXIF removal
│   │   │   ├── ai_service.py       # OpenAI Vision API classification
│   │   │   ├── hotspot_service.py  # DBSCAN clustering
│   │   │   ├── metrics_service.py  # Metric calculations
│   │   │   └── notification_service.py # Email notifications
│   │   │
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   └── celery_tasks.py     # Async image classification, hotspot detection
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── s3.py               # AWS S3 helpers
│   │       ├── email.py            # Email sending
│   │       └── validators.py       # Custom validators
│   │
│   ├── migrations/                 # Alembic DB migrations (future)
│   ├── tests/                      # pytest test suite (future)
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment template
│   └── Dockerfile                  # Docker image (future)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React entry point
│   │   ├── App.tsx                 # Root component
│   │   ├── index.css               # Global styles
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Report.tsx          # Citizen report form
│   │   │   ├── Dashboard.tsx       # Officer dashboard
│   │   │   ├── PublicMetrics.tsx   # Public cleanliness dashboard
│   │   │   ├── Login.tsx
│   │   │   └── NotFound.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── PhotoUpload.tsx
│   │   │   ├── Map.tsx
│   │   │   ├── TaskCard.tsx
│   │   │   ├── WardRanking.tsx
│   │   │   └── Hotspot.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useComplaints.ts
│   │   │   └── useLocation.ts
│   │   │
│   │   ├── store/
│   │   │   ├── authStore.ts        # Zustand auth state
│   │   │   └── complaintStore.ts
│   │   │
│   │   ├── api/
│   │   │   └── client.ts           # Axios API client
│   │   │
│   │   ├── utils/
│   │   │   ├── localStorage.ts
│   │   │   └── formatters.ts
│   │   │
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   │
│   │   └── public/
│   │       ├── manifest.json       # PWA manifest
│   │       ├── cleanloop.svg       # Logo
│   │       └── sw.js              # Service worker (future)
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── docker-compose.yml              # Local dev stack (PostgreSQL, Redis, LocalStack)
├── .env.example                    # Environment variables template
├── PRD.md                          # Product requirements
├── README.md                       # Project setup guide
└── .gitignore
```

## Key Files Created (Phase 1)

✅ **Backend**
- `backend_main.py` → FastAPI app with CORS, health check, lifespan
- `backend_database.py` → PostgreSQL + PostGIS connection, session factory
- `backend_models.py` → SQLAlchemy ORM (User, Ward, Complaint, Assignment, Hotspot, WardMetric)
- `backend_schemas.py` → Pydantic request/response models for API validation

✅ **Frontend**
- `frontend_main.tsx` → React entry point with PWA service worker registration
- `frontend_App.tsx` → Root component (hero section + 3 main feature cards)
- `frontend_index.html` → HTML template with PWA meta tags
- `frontend_index.css` → Global Tailwind styles
- `vite.config.ts` → Vite bundler config with API proxy to backend
- `frontend_manifest.json` → PWA manifest for mobile app installation

✅ **Infrastructure**
- `requirements.txt` → Python dependencies (FastAPI, SQLAlchemy, PostGIS, Celery, etc.)
- `docker-compose.yml` → PostgreSQL (PostGIS), Redis, LocalStack S3 stack
- `.env.example` → Template for environment variables
- `frontend_package.json` → React + Tailwind + Vite dependencies

## Next Steps (Phase 2)

1. **Set up backend directory structure** → Create `app/api/`, `app/services/`, `app/workers/` folders
2. **Implement Auth Routes** → User registration, login, JWT tokens
3. **Implement Complaint Routes** → POST (create), GET (list), PATCH (update status)
4. **Integrate OpenAI Vision API** → Image classification service
5. **Implement Hotspot Detection** → DBSCAN clustering Celery task
6. **Setup React pages** → Report form, Officer dashboard, Public metrics
7. **Database migrations** → Alembic setup for schema versioning
8. **Testing** → Unit tests for services, integration tests for API
