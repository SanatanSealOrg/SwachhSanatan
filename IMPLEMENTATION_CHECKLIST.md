# CleanLoop Implementation Checklist

**Project**: Community Waste & Sanitation Intelligence for Chennai  
**Timeline**: 6 months solo development  
**Status**: ✅ Phase 0 Complete (Foundation Scaffolding)  

---

## ✅ Phase 0: Project Foundation (COMPLETE)

### Documentation
- [x] **PRD.md** — 15-section product requirements document
  - Problem statement, solution overview, 3 user flows
  - 6-month feature breakdown (3 phases: 8 weeks core, 8 weeks hotspots+dashboard, 8 weeks polish)
  - Technical architecture, database schema, API spec
  - Success metrics, risks, launch plan

- [x] **README.md** — Quick start guide + project overview
- [x] **SETUP.md** — Detailed environment setup + troubleshooting
- [x] **PROJECT_STRUCTURE.md** — Directory layout + file organization

### Backend Foundation
- [x] **backend_main.py** — FastAPI app with CORS, health check, lifespan
- [x] **backend_database.py** — PostgreSQL + PostGIS connection, session factory
- [x] **backend_models.py** — SQLAlchemy ORM models:
  - User (citizen, officer, admin)
  - Ward (Chennai municipal divisions)
  - Complaint (core entity with AI metadata)
  - Assignment (officer tasks)
  - Hotspot (chronic problem areas)
  - WardMetric (daily aggregates)
- [x] **backend_schemas.py** — Pydantic request/response schemas

### Frontend Foundation
- [x] **frontend_main.tsx** — React entry point with PWA service worker
- [x] **frontend_App.tsx** — Root component (hero + 3 feature cards)
- [x] **frontend_index.html** — HTML template with PWA meta tags
- [x] **frontend_index.css** — Tailwind global styles
- [x] **frontend_manifest.json** — PWA manifest for mobile installation
- [x] **vite.config.ts** — Vite bundler config + API proxy

### Infrastructure & Dependencies
- [x] **requirements.txt** — Python dependencies (23 packages)
  - FastAPI, SQLAlchemy, PostGIS, Celery, Redis, Pillow, scikit-image, OpenAI, boto3
- [x] **docker-compose.yml** — Development stack:
  - PostgreSQL 16 with PostGIS
  - Redis 7 (caching + task queue)
  - LocalStack (S3 mock)
- [x] **frontend_package.json** — React + Tailwind + Vite dependencies
- [x] **.env.example** — Environment variables template
- [x] **.gitignore** — Git ignore patterns

---

## 📋 Phase 1: Core Reporting & Officer Dashboard (Weeks 1-8)

### Week 1-2: Backend Setup
- [ ] Organize files into `backend/app/` subdirectories:
  - [ ] `backend/app/api/` — Route modules
  - [ ] `backend/app/services/` — Business logic
  - [ ] `backend/app/workers/` — Celery tasks
  - [ ] `backend/app/utils/` — Helpers
- [ ] Set up Alembic for database migrations
  - [ ] Create initial migration from models
  - [ ] Test migration workflow
- [ ] Set up pytest + test suite structure

### Week 2-3: Authentication
- [ ] Implement `backend/app/api/auth.py`:
  - [ ] `POST /api/auth/register` — User registration
  - [ ] `POST /api/auth/login` — Login + JWT token
  - [ ] `POST /api/auth/logout` — Logout
- [ ] Implement `backend/app/services/auth_service.py`:
  - [ ] Password hashing (bcrypt)
  - [ ] JWT token generation/verification
  - [ ] User validation
- [ ] Unit tests for auth (80%+ coverage)

### Week 3-4: Citizen Report API
- [ ] Implement `backend/app/api/complaints.py`:
  - [ ] `POST /api/complaints` — Create complaint with photo
  - [ ] `GET /api/complaints/<id>` — Get single complaint
  - [ ] `GET /api/complaints?ward_id=<id>&status=open` — List complaints
  - [ ] `PATCH /api/complaints/<id>` — Update status
- [ ] Implement `backend/app/services/image_service.py`:
  - [ ] Photo upload to S3
  - [ ] Image compression (<2MB)
  - [ ] EXIF metadata stripping
  - [ ] Thumbnail generation
- [ ] Integration tests for complaint flow

### Week 4-5: Image Classification (AI)
- [ ] Implement `backend/app/services/ai_service.py`:
  - [ ] OpenAI Vision API integration
  - [ ] Waste type detection (bin, dumping, construction, biohazard)
  - [ ] Confidence scoring
  - [ ] Error handling + fallback
- [ ] Implement `backend/app/workers/celery_tasks.py`:
  - [ ] Async image classification job
  - [ ] Result storage in complaint record
  - [ ] Retry logic
- [ ] Test image classification on sample dataset (80%+ accuracy target)

### Week 5-6: Officer Assignment
- [ ] Implement `backend/app/api/assignments.py`:
  - [ ] `GET /api/assignments?assigned_to=<officer_id>&status=pending` — Officer tasks
  - [ ] `PATCH /api/assignments/<id>` — Update task status (accept, in_progress, complete)
- [ ] Implement auto-assignment logic:
  - [ ] Route to nearest ward officer
  - [ ] Handle manual reassignment
- [ ] Implement `backend/app/services/notification_service.py`:
  - [ ] Email notifications on complaint submission
  - [ ] Email notifications on status change
  - [ ] SLA overdue warnings

### Week 6-7: Frontend — Citizen Report Form
- [ ] Organize frontend into `frontend/src/pages/` and `frontend/src/components/`
- [ ] Implement citizen report page:
  - [ ] `frontend/src/pages/Report.tsx` — Report form UI
  - [ ] `frontend/src/components/PhotoUpload.tsx` — Camera + upload
  - [ ] `frontend/src/components/Map.tsx` — Location picker (Leaflet)
  - [ ] Waste type dropdown, severity slider, description
- [ ] Implement offline mode:
  - [ ] Service worker for PWA
  - [ ] Queue reports when offline
  - [ ] Sync on reconnect
- [ ] Implement API client:
  - [ ] `frontend/src/api/client.ts` — Axios instance
  - [ ] Auth token management (JWT from localStorage)

### Week 7-8: Frontend — Officer Dashboard
- [ ] Implement officer dashboard page:
  - [ ] `frontend/src/pages/Dashboard.tsx` — Main dashboard
  - [ ] `frontend/src/components/TaskCard.tsx` — Individual task card
  - [ ] Task list with filtering (open, assigned, in_progress)
  - [ ] Priority ranking (severity + age + frequency)
- [ ] Implement task detail page:
  - [ ] View photos + location on map
  - [ ] Accept/reassign buttons
  - [ ] Mark in-progress, completed
  - [ ] Upload before/after photos
- [ ] Implement Zustand stores:
  - [ ] `frontend/src/store/authStore.ts` — Auth state
  - [ ] `frontend/src/store/complaintStore.ts` — Complaint state

### Week 8: Testing & Deployment Setup
- [ ] End-to-end testing:
  - [ ] Register as citizen → submit complaint → receive ticket
  - [ ] Officer receives notification → marks in-progress → resolves
  - [ ] Citizen sees status updates
- [ ] Docker image creation:
  - [ ] `backend/Dockerfile` — FastAPI image
  - [ ] `frontend/Dockerfile` — React build + serve
- [ ] CI/CD setup:
  - [ ] GitHub Actions workflow (lint, test, build)
  - [ ] Deploy to staging on PR
- [ ] Performance benchmarks:
  - [ ] API response time <500ms p95
  - [ ] Image upload <5s for 2G connection

**Deliverable**: Functional end-to-end flow; officers can receive & resolve complaints

---

## 📊 Phase 2: Hotspots & Public Dashboard (Weeks 9-16)

### Week 9-10: Hotspot Detection
- [ ] Implement `backend/app/services/hotspot_service.py`:
  - [ ] DBSCAN clustering (eps=100m, min_samples=3)
  - [ ] Hotspot creation/update logic
  - [ ] Chronic escalation (>7 days, >5 reports)
- [ ] Implement `backend/app/workers/celery_tasks.py`:
  - [ ] Weekly batch job (Sunday 2 AM IST)
  - [ ] Fetch complaints from past 7 days
  - [ ] Run clustering, store hotspots
  - [ ] Auto-escalate chronic hotspots
- [ ] Implement `backend/app/api/hotspots.py`:
  - [ ] `GET /api/hotspots?ward_id=<id>` — Get hotspots
- [ ] Test hotspot detection on 1000+ complaint dataset

### Week 10-11: Ward Metrics Calculation
- [ ] Implement `backend/app/services/metrics_service.py`:
  - [ ] Daily aggregation job (12 AM IST)
  - [ ] Complaint count, resolved count, avg resolution time
  - [ ] Cleanliness score (0-100 formula)
  - [ ] Cache in Redis (expire 12 AM next day)
- [ ] Implement `backend/app/api/metrics.py`:
  - [ ] `GET /api/metrics/wards?date=2024-01-15` — Get all ward metrics
  - [ ] `GET /api/metrics/wards/<id>/history?days=30` — Historical data
- [ ] Test metric calculations on sample data

### Week 11-12: Public Dashboard Frontend
- [ ] Implement public dashboard page:
  - [ ] `frontend/src/pages/PublicMetrics.tsx` — Main dashboard
  - [ ] `frontend/src/components/WardRanking.tsx` — Leaderboard table
  - [ ] Sortable by complaint volume, resolution rate, response time
- [ ] Implement ward map:
  - [ ] Leaflet map with ward polygons (PostGIS geometry)
  - [ ] Color coding: Green (<10 complaints, >85% resolved), Yellow (10-30, 70-85%), Red (>30 or <70%)
  - [ ] Click ward → drill into hotspots
  - [ ] Click hotspot → see incident photos + timeline
- [ ] Implement hotspot details component:
  - [ ] Photo gallery, map pin, timeline
  - [ ] Resident comments (optional for MVP)

### Week 12-13: Before/After Verification
- [ ] Implement `backend/app/services/image_service.py`:
  - [ ] SSIM (Structural Similarity Index) comparison
  - [ ] Histogram-based change detection
  - [ ] Threshold: SSIM > 0.85 = likely unresolved
- [ ] Update assignment completion:
  - [ ] Officer uploads before/after photos
  - [ ] System auto-verifies
  - [ ] Flag for manual review if similarity high
- [ ] Unit tests for image comparison

### Week 13-14: Escalation Rules
- [ ] Implement auto-escalation logic:
  - [ ] If assignment overdue >48hrs → escalate to senior officer
  - [ ] If hotspot chronic >7 days → escalate
  - [ ] Escalated assignments get email notification
- [ ] Implement `backend/app/workers/celery_tasks.py`:
  - [ ] Escalation check job (runs every 6 hours)
- [ ] Test escalation workflow

### Week 14-16: Mobile Optimization & Testing
- [ ] PWA offline mode:
  - [ ] Service worker caching strategy (cache-first for assets)
  - [ ] Background sync for queued reports
  - [ ] Workbox integration
- [ ] Responsive design:
  - [ ] Test on iPhone 12, Android phones
  - [ ] Touch-friendly buttons, readable text on 4" screens
  - [ ] Optimize images for low bandwidth (2G fallback)
- [ ] UAT with officers:
  - [ ] Weekly sync with 2 pilot ward officers
  - [ ] Iterate on dashboard based on feedback
  - [ ] Fix critical bugs within 24 hrs
- [ ] Integration tests:
  - [ ] Full flow: report → cluster → hotspot → dashboard visible
  - [ ] Performance tests: dashboard loads <2s with 1000 complaints

**Deliverable**: Public dashboard live; hotspots visible; mobile app works offline

---

## 🎯 Phase 3: Polish & Launch (Weeks 17-24)

### Week 17-18: Performance Optimization
- [ ] Database optimization:
  - [ ] PostGIS spatial indexes verified
  - [ ] Query execution time <500ms p95
  - [ ] Add pagination for large datasets
- [ ] Caching strategy:
  - [ ] Redis cache for ward metrics
  - [ ] Cache invalidation on complaint update
- [ ] CDN setup:
  - [ ] CloudFront for images + frontend assets
  - [ ] Test latency from Chennai

### Week 18-19: Privacy & Compliance
- [ ] GDPR/India data protection:
  - [ ] Consent flow before data collection
  - [ ] Anonymous report option
  - [ ] Data deletion API (`DELETE /api/users/<id>` cascade)
- [ ] Image privacy:
  - [ ] Verify EXIF stripping on all uploads
  - [ ] S3 lifecycle policy: delete after 2 years
- [ ] Data minimization audit:
  - [ ] Review what data is collected
  - [ ] Remove unnecessary fields
- [ ] Privacy policy + ToS:
  - [ ] Draft documents in English (Tamil translation later)

### Week 19-20: Light Gamification
- [ ] Citizen badges:
  - [ ] "Top Reporter" (most reports in month)
  - [ ] "Issue Resolver" (reported issue got resolved)
- [ ] Ward leaderboard:
  - [ ] Best (lowest complaint volume, highest resolution rate)
  - [ ] Worst (highest complaints, lowest resolution rate)
- [ ] Update public dashboard to show badges

### Week 20-21: Documentation & Training
- [ ] API documentation:
  - [ ] OpenAPI/Swagger spec (auto-generated by FastAPI)
  - [ ] Postman collection for testing
- [ ] Deployment guide:
  - [ ] Step-by-step deployment to Railway/Render
  - [ ] Environment variables setup
  - [ ] Database backup strategy
- [ ] Officer training deck:
  - [ ] How to use dashboard (PDF + video)
  - [ ] Workflow: view task → assign → mark progress → verify → close
  - [ ] FAQ: common issues, troubleshooting

### Week 21-23: Beta Launch Preparation
- [ ] Stakeholder alignment:
  - [ ] Secure 1 ward partnership (Chennai Corporation)
  - [ ] Get 2 ward officers as pilot users
  - [ ] Collect ward boundary GeoJSON
  - [ ] Set SLA expectations (response time, resolution target)
- [ ] Citizen recruitment:
  - [ ] Recruit 50-100 citizen testers (WhatsApp groups, NGOs)
  - [ ] Create onboarding video (2 min, Tamil subtitles)
  - [ ] Set up help email/phone
- [ ] Monitoring setup:
  - [ ] Application metrics (API response time, error rate)
  - [ ] Business metrics (complaints/day, resolution rate, hotspots detected)
  - [ ] User metrics (daily active citizens, officer logins)
- [ ] Incident response plan:
  - [ ] On-call rotation (initially just you)
  - [ ] Bug fix SLA (<4 hrs for critical)
  - [ ] Escalation process

### Week 23-24: Beta Testing & Iteration
- [ ] Monitor metrics daily:
  - [ ] Citizen adoption, complaint volume, resolution rate
  - [ ] API performance, error logs
- [ ] Weekly sync with officers:
  - [ ] Iterate UI based on feedback
  - [ ] Fix critical bugs within 24 hrs
- [ ] Post-resolution citizen surveys:
  - [ ] "Was complaint resolved satisfactorily?" (1-5 stars)
  - [ ] Collect suggestions
- [ ] Plan Phase 2 features:
  - [ ] Contractor app (route optimization, GPS tracking)
  - [ ] Predictive hotspot forecasting
  - [ ] Multi-language support (Tamil)
  - [ ] Integration with municipality ticketing (IMIS)

**Deliverable**: Beta-ready product; ready for live launch in 1 ward

---

## 📈 Success Criteria

### Technical Metrics
- [ ] API response time <500ms p95
- [ ] Image classification accuracy ≥80% (validated manually)
- [ ] Uptime ≥99%
- [ ] PWA offline sync ≥95% success rate
- [ ] Database query time <100ms p95

### Operational Metrics
- [ ] 500+ citizen users in pilot ward
- [ ] 100+ complaints submitted per week
- [ ] ≥80% of complaints resolved within 48 hrs
- [ ] <24 hrs average response time (open → assigned)
- [ ] 3-5 chronic hotspots identified + escalated

### User Satisfaction
- [ ] 2/2 pilot ward officers actively using dashboard daily
- [ ] ≥4/5 stars for citizen report experience (post-resolution survey)
- [ ] ≥85% of citizens confirm AI waste type classification

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Solo dev burnout | Delays all phases | Break into smaller tasks, take breaks, automate repetitive work |
| AI misclassification | Officers distrust system | Human-in-the-loop: officer confirms before routing (Phase 2+) |
| Officer adoption fails | Dashboard unused | Weekly sync with officers, iterate UI aggressively |
| GPS accuracy in urban canyon | Wrong location | Allow manual address entry, fallback to geocoding API |
| S3 costs spike | Budget overrun | Compress to <1MB, delete after 2 years, use LocalStack for dev |
| Database performance | Slow hotspot clustering | Test DBSCAN on 10K+ complaints early, optimize indexes |
| PostgreSQL PostGIS bugs | Data corruption | Always backup before major ops, test migrations in staging |
| Officer initial training low | Poor adoption | Make dashboard FASTER than current workflow, 1-on-1 demos |

---

## 🎯 Key Dates

- **Week 1** — Start Phase 1 development
- **Week 8** — Phase 1 complete; core flow working
- **Week 9** — Start Phase 2 development
- **Week 16** — Phase 2 complete; public dashboard live
- **Week 17** — Start Phase 3 (polish + launch prep)
- **Week 24** — Beta launch ready in 1 ward

---

## 📞 Communication

- **Daily**: Check app logs, metrics dashboard
- **Weekly**: Sync with pilot officers (Thursdays 2 PM IST)
- **Bi-weekly**: Review PRD against progress, adjust roadmap if needed
- **Monthly**: Community town hall (if Beta users >50)

---

**Status**: 🟢 Phase 0 Complete (Foundation)  
**Next**: Start Phase 1 Week 1 development

Last Updated: 2024  
Estimated Completion: 6 months
