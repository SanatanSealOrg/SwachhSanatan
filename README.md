# CleanLoop: Community Waste & Sanitation Intelligence

**Status**: Alpha Development  
**Target**: MVP Launch in 6 months (Chennai, India)  
**Tech**: Python + FastAPI | React + PWA | PostgreSQL + PostGIS  

---

## 📋 Overview

CleanLoop is an AI-powered waste management platform that connects citizens, ward officers, and municipalities to improve urban sanitation through:

✅ **Citizen Reporting** — Photo + GPS to report overflowing bins & illegal dumping  
✅ **Officer Dashboard** — AI-ranked priority tasks + hotspot clustering  
✅ **Public Metrics** — Ward-by-ward cleanliness leaderboard + accountability  

---

## 🚀 Quick Start

### Prerequisites
- winget , Git

### Setup (5 min)

```bash
# 1. Clone repo
git clone https://github.com/yourusername/cleanloop.git
cd cleanloop

# 2. Copy environment
cp .env.example .env

# 3. Start infrastructure (PostgreSQL, Redis, S3)
docker-compose up -d

# 4. Backend
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend_main:app --reload

# 5. Frontend (new terminal)
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
cleanloop/
├── backend_main.py           # FastAPI app
├── backend_database.py       # PostgreSQL + PostGIS
├── backend_models.py         # SQLAlchemy ORM
├── backend_schemas.py        # Pydantic validation
├── requirements.txt
│
├── frontend_main.tsx         # React entry
├── frontend_App.tsx          # Root component
├── frontend_package.json
├── vite.config.ts
│
├── docker-compose.yml        # Dev infrastructure
├── .env.example
│
├── PRD.md                    # Product specification (15 sections)
├── SETUP.md                  # Detailed setup guide
├── PROJECT_STRUCTURE.md      # Directory layout
└── README.md                 # This file
```

---

## 🗂️ Current Phase

**Phase 1: Core Foundation (Weeks 1-8)**

- [x] PRD documentation
- [x] Project scaffolding
- [x] Backend models (User, Complaint, Assignment, Hotspot, Ward, Metrics)
- [x] Frontend skeleton (React + Tailwind)
- [x] Infrastructure (docker-compose: Postgres, Redis, S3)
- [ ] Auth routes (register, login, JWT)
- [ ] Complaint API (create, list, update)
- [ ] Image upload + OpenAI classification
- [ ] Officer dashboard UI
- [ ] Database migrations

---

## 📊 Architecture

```
Citizen App (PWA)
    ↓
    └─→ FastAPI Backend
        ├─→ PostgreSQL + PostGIS (complaints, hotspots, metrics)
        ├─→ Redis (cache, task queue)
        ├─→ Celery (async image classification)
        └─→ S3 (image storage)

Officer Dashboard (React)
    ↓
    └─→ Same Backend

Public Dashboard (React)
    ↓
    └─→ Same Backend (read-only metrics)
```

---

## 🎯 Success Metrics (6-Month MVP Target)

| Metric | Target |
|--------|--------|
| Citizen Adoption | 500+ users in pilot ward |
| Complaint Volume | 100+ per week |
| Resolution Rate | ≥80% within 48 hrs |
| Response Time | <24 hrs (open → assigned) |
| Hotspot Accuracy | 3-5 chronic areas detected |

---

## 🛠️ Tech Stack Rationale

| Component | Choice | Why |
|-----------|--------|-----|
| Backend | FastAPI + Python | Async for image processing, excellent ML integration |
| Database | PostgreSQL + PostGIS | Spatial queries for geolocation & clustering |
| Frontend | React + PWA | Mobile-first, works offline, no app store friction |
| Caching | Redis | Fast dashboard metrics, task queue for Celery |
| Images | S3 + Pillow | Scalable, CDN-ready, compression |
| AI | OpenAI Vision API | No training needed, 80%+ accuracy out of box |
| Clustering | scikit-learn DBSCAN | Efficient hotspot detection |
| Deployment | Docker + Railway/Render | Solo-dev friendly, auto-scaling |

---

## 📝 Next Steps

### Immediate (This Week)
1. Organize files into `backend/app/` and `frontend/src/` directories
2. Set up Alembic for database migrations
3. Implement auth routes (register, login)
4. Create unit tests for auth service

### Phase 1 (Next 7 weeks)
- Complaint CRUD + image upload
- OpenAI image classification service
- Officer dashboard mockup
- Citizen report form

### Phase 2 (Weeks 9-16)
- Hotspot detection (DBSCAN)
- Public dashboard
- Escalation rules
- PWA offline mode

### Phase 3 (Weeks 17-24)
- Performance optimization
- Privacy compliance (GDPR consent, EXIF stripping)
- Beta launch (1 ward + 100 citizens + 2 officers)

---

## 🤝 Contributing

### Local Development
```bash
# Activate venv
source venv/bin/activate

# Run backend with reload
python -m uvicorn backend_main:app --reload

# Run frontend with hot reload
npm run dev
```

### Code Style
- Backend: PEP 8 (use `flake8` for linting)
- Frontend: ESLint + Prettier (configured in `package.json`)

### Testing
```bash
pytest tests/ -v          # Backend
npm run test              # Frontend
```

---

## 📖 Documentation

- **[PRD.md](./PRD.md)** — 15-section product specification
- **[SETUP.md](./SETUP.md)** — Detailed setup & troubleshooting
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** — Directory layout & file organization
- **[API Routes](./backend_main.py)** — FastAPI endpoint stubs
- **[Database Schema](./backend_models.py)** — SQLAlchemy ORM models

---

## 🔐 Security Notes

- **Secret Key**: Change `SECRET_KEY` in `.env` before production
- **CORS**: Restrict `ALLOWED_ORIGINS` to your domain
- **Image Privacy**: Strip EXIF data on upload; never store raw coordinates in image metadata
- **Rate Limiting**: Add rate limits on public endpoints (TODO: Phase 2)
- **Data Retention**: Delete images after 2 years (S3 lifecycle policy)

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is free
lsof -i :8000

# Check PostgreSQL
docker logs $(docker-compose ps -q postgres)
```

### Frontend build fails
```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection error
```bash
# Verify .env DATABASE_URL
cat .env | grep DATABASE_URL

# Reset containers
docker-compose down -v
docker-compose up -d
```

---

## 📞 Support

**Questions?**
- Check [PRD.md](./PRD.md) for product specs
- Check [SETUP.md](./SETUP.md) for setup issues
- Create a GitHub Issue for bugs

---

## 📄 License

MIT License — See LICENSE file for details

---

**Built with ❤️ for Chennai's cleaner future** 🇮🇳

Last Updated: 2024
