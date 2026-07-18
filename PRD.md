# CleanLoop: Community Waste & Sanitation Intelligence
## Product Requirements Document

**Status**: MVP Scope for Solo Development  
**Timeline**: 6 months  
**Location**: Chennai, India  
**Tech Stack**: Python + FastAPI | React + PWA | PostgreSQL + PostGIS  
**Developer**: Solo  

---

## 1. Executive Summary

**CleanLoop** is a community-driven waste management platform that bridges citizens, ward officers, and sanitation contractors through AI-powered complaint mapping, hotspot detection, and accountability tracking.

### Core Value Proposition
- **Citizens**: Report overflowing bins/illegal dumping via photo + GPS → track resolution in real-time
- **Ward Officers**: AI-prioritized complaint list + hotspot clustering → focus on chronic problems
- **Municipality**: Public cleanliness dashboard → ward rankings + accountability + cost savings

### Launch City
**Chennai** — 6.3M population, 200+ wards, high waste density variation

---

## 2. Problem Statement

### For Citizens
- Complaints to municipal helplines disappear; no tracking
- Repeated overflowing bins in same locations never get fixed
- No visibility into whether pickup actually occurred

### For Ward Officers
- Flooded with unstructured WhatsApp complaints
- No prioritization mechanism; ad-hoc response
- Difficult to identify systemic problem areas

### For Municipality
- No data-driven sanitation metrics
- Can't benchmark wards or measure improvement
- Political pressure without evidence

---

## 3. Solution Overview

### Three-Tier Architecture

**Tier 1: Citizen Reporting**
- Mobile-first web app (PWA)
- Photo + GPS + description
- Auto-detection of waste type & severity (AI)
- Real-time ticket number + status tracking

**Tier 2: Officer Dashboard**
- AI-ranked priority list (severity + frequency + age)
- Assign to contractor/crew
- Mark in-progress, resolved, or escalate
- Before/after photo upload for verification

**Tier 3: Public Dashboard**
- Ward-by-ward cleanliness scores
- Complaint volume, resolution rate, avg response time
- Hotspot map (chronic problem areas)
- Leaderboard (best/worst performing wards)

---

## 4. Core User Flows

### Flow 1: Citizen Reports Waste (MVP Critical Path)

```
START: Citizen opens web app
  ├─ Take photo OR upload existing image
  ├─ System auto-detects: location (GPS), waste type (AI)
  ├─ Citizen confirms/edits: address, description
  ├─ Submit complaint
  └─ END: Show ticket #, map pin, "status: open"

Expected timeline: < 2 min from camera to submission
```

**Acceptance Criteria**:
- Photo upload works on slow 2G (compress to <2MB)
- GPS fallback: allow manual address entry if GPS fails
- Offline mode: queue report, sync when reconnected
- AI classification: 80%+ accuracy on waste type

---

### Flow 2: Complaint Auto-Assigned to Officer

```
START: Complaint submitted
  ├─ Backend clusters complaints by location (100m radius)
  ├─ AI groups: "hotspot detected — 5 reports this week"
  ├─ System assigns to nearest ward officer
  ├─ Officer receives notification (email + in-app)
  └─ END: Officer sees task in dashboard

Expected timeline: < 5 sec from submission to notification
```

**Acceptance Criteria**:
- Geospatial clustering works (DBSCAN, 100m eps)
- Officer sees 3-5 top-priority tasks per day
- Assignment logic: nearest office OR contractor coverage zone
- Notification: email + in-app badge

---

### Flow 3: Officer Updates Status & Resolves

```
START: Officer sees complaint in dashboard
  ├─ Clicks "Assign to contractor" OR "Will handle myself"
  ├─ Task moves to "assigned" status
  ├─ Officer marks "in-progress" when crew departs
  ├─ Officer uploads before/after photos
  ├─ System compares images (SSIM check)
  ├─ If similarity > 0.85: flag "may be unresolved"
  ├─ Otherwise: mark "resolved"
  └─ END: Citizen notified, complaint archived

Expected timeline: 24–48 hrs (based on SLA)
```

**Acceptance Criteria**:
- Status workflow enforced (open → assigned → in-progress → resolved)
- Photo upload + SSIM comparison (reject if <0.5 change detected)
- Escalation trigger: if overdue, auto-notify senior officer
- Citizen gets push/email on state change

---

### Flow 4: Public Dashboard View

```
START: Anonymous user visits cleanloop.city/dashboard
  ├─ See map of all wards with color coding:
  │   - Green: <10 complaints/week, >85% resolved
  │   - Yellow: 10-30 complaints/week, 70-85% resolved
  │   - Red: >30 complaints/week OR <70% resolved
  ├─ Click ward → see hotspots + incident history
  ├─ Click hotspot → see all photos + timeline
  └─ END: View ward rankings (sortable by metric)

Expected timeline: Dashboard loads < 2s
```

**Acceptance Criteria**:
- Map renders all wards with PostGIS geometry
- Color coding updates daily (12 AM IST)
- Hotspot drill-down shows 10 most recent incidents
- Metric calculation: complaints in past 30 days

---

## 5. Feature Breakdown (6-Month MVP)

### Phase 1: Weeks 1–8 (Core Reporting + Officer Dashboard)

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| **Citizen App** | P0 | 3 wks | Photo upload, GPS, form submit, ticket view |
| **Officer Dashboard** | P0 | 3 wks | List view, status update, bulk assign |
| **Auth + Roles** | P0 | 2 wks | JWT, 3 roles (citizen/officer/admin) |
| **Basic Routing** | P1 | 1 wk | Manual assignment logic |
| **Database Schema** | P0 | 1 wk | Postgres + PostGIS, migrations |
| **Image Storage** | P0 | 1 wk | S3 integration, thumbnail generation |
| **Email Notifications** | P1 | 1 wk | Complaint submitted, status changed, overdue |
| **AI Image Classification** | P1 | 2 wks | OpenAI Vision API (no fine-tuning) |
| **Docker + Deployment** | P0 | 1 wk | Basic CI/CD pipeline |

**Deliverable**: Functional end-to-end flow; officers can assign and resolve complaints

---

### Phase 2: Weeks 9–16 (Hotspots + Public Dashboard)

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| **Hotspot Detection** | P1 | 2 wks | DBSCAN clustering, weekly batch job |
| **Public Dashboard** | P1 | 3 wks | Map rendering, ward metrics, leaderboard |
| **Ward Metrics Calculation** | P1 | 1 wk | Daily aggregation: complaints, resolution rate, avg time |
| **Before/After Verification** | P2 | 2 wks | SSIM comparison, verification workflow |
| **Escalation Rules** | P2 | 1 wk | Auto-escalate if overdue or chronic hotspot |
| **Mobile Optimization** | P1 | 2 wks | PWA offline mode, responsive design |
| **Testing + Bug Fixes** | P0 | 2 wks | Unit tests, integration tests, UAT with officers |

**Deliverable**: Public dashboard live; hotspots visible; mobile app works offline

---

### Phase 3: Weeks 17–24 (Polish + Launch Prep)

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| **Performance Tuning** | P1 | 1 wk | Database indexing, caching strategy, CDN for images |
| **Gamification (Light)** | P2 | 1 wk | Citizen badges ("Top Reporter"), ward leaderboard |
| **Privacy Compliance** | P0 | 2 wks | GDPR consent flow, EXIF stripping, data deletion API |
| **Documentation + Handoff** | P1 | 1 wk | API docs, deployment guide, officer training deck |
| **Contractor Portal** | P3 | 0 wks | **OUT OF SCOPE** — defer to Phase 2 |
| **Predictive ML** | P3 | 0 wks | **OUT OF SCOPE** — defer to Phase 2 |
| **Beta Launch** | P0 | 2 wks | 1 ward + 100 citizens + 2 officers; iterate on feedback |

**Deliverable**: Beta-ready product; can go live with 1 ward

---

## 6. Technical Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Frontend Layer                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ React (web) + PWA (mobile)                          │ │
│ │ - Citizen: Report form, ticket tracking             │ │
│ │ - Officer: Dashboard, assignment, photo upload      │ │
│ │ - Public: Dashboard, ward rankings, hotspot map     │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API (JSON)
┌──────────────────▼──────────────────────────────────────┐
│ Backend Layer (Python + FastAPI)                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ API Routes:                                         │ │
│ │ - /api/complaints (POST, GET, PATCH)                │ │
│ │ - /api/assignments (GET, PATCH)                     │ │
│ │ - /api/hotspots (GET)                               │ │
│ │ - /api/metrics/wards (GET)                          │ │
│ │ - /api/auth (POST login/register)                   │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Service Layer:                                      │ │
│ │ - ImageClassificationService (OpenAI Vision)        │ │
│ │ - HotspotDetectionService (DBSCAN batch)            │ │
│ │ - NotificationService (email + SMS)                 │ │
│ │ - MetricsCalculationService (daily aggregation)     │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ Data Layer                                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ PostgreSQL (primary)                                │ │
│ │ - complaints, assignments, users, wards, hotspots   │ │
│ │ - PostGIS extension for spatial queries             │ │
│ │ - Indexes: (ward_id, status), location GIST         │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Redis (caching + async tasks)                       │ │
│ │ - Cache: ward metrics (expire daily at 12 AM IST)   │ │
│ │ - Queue: image classification jobs (Celery)         │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ S3 (image storage)                                  │ │
│ │ - Bucket: cleanloop-images                          │ │
│ │ - Lifecycle: delete after 2 years                   │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Database Schema (Core Tables)

```sql
-- Users (polymorphic: citizen, officer, admin)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  phone VARCHAR UNIQUE,
  password_hash VARCHAR,
  user_type ENUM('citizen', 'officer', 'admin'),
  ward_id UUID REFERENCES wards(id),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Wards (Chennai municipal divisions)
CREATE TABLE wards (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  ward_number INT,
  geometry GEOMETRY(POLYGON, 4326),  -- PostGIS
  population INT,
  PRIMARY OFFICER contact_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Complaints (core entity)
CREATE TABLE complaints (
  id UUID PRIMARY KEY,
  citizen_id UUID NOT NULL REFERENCES users(id),
  ward_id UUID NOT NULL REFERENCES wards(id),
  location GEOMETRY(POINT, 4326),  -- GPS coordinate
  waste_type VARCHAR,  -- enum: bin, dumping, construction, biohazard
  severity_score INT CHECK (severity_score BETWEEN 1 AND 5),
  description TEXT,
  image_urls TEXT[],  -- S3 paths
  status ENUM('open', 'assigned', 'in_progress', 'resolved', 'rejected'),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP,
  
  -- AI metadata
  ai_waste_type VARCHAR,
  ai_confidence FLOAT CHECK (ai_confidence BETWEEN 0 AND 1),
  hotspot_id UUID REFERENCES hotspots(id),
  
  INDEX idx_location (location),
  INDEX idx_ward_status (ward_id, status),
  INDEX idx_created (created_at DESC)
);

-- Assignments (complaint → officer/contractor)
CREATE TABLE assignments (
  id UUID PRIMARY KEY,
  complaint_id UUID NOT NULL REFERENCES complaints(id) UNIQUE,
  assigned_to UUID NOT NULL REFERENCES users(id),
  status ENUM('pending', 'accepted', 'in_progress', 'completed', 'escalated'),
  assigned_at TIMESTAMP DEFAULT NOW(),
  due_at TIMESTAMP,
  completed_at TIMESTAMP,
  completion_image_url VARCHAR,
  verified BOOLEAN DEFAULT FALSE,
  verification_ssim_score FLOAT,
  INDEX idx_assigned_to_status (assigned_to, status)
);

-- Hotspots (clustered chronic issues)
CREATE TABLE hotspots (
  id UUID PRIMARY KEY,
  ward_id UUID NOT NULL REFERENCES wards(id),
  centroid GEOMETRY(POINT, 4326),
  incident_count INT DEFAULT 0,
  first_reported TIMESTAMP,
  last_reported TIMESTAMP,
  status ENUM('active', 'resolved', 'chronic'),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Ward metrics (daily aggregates for dashboard)
CREATE TABLE ward_metrics (
  id UUID PRIMARY KEY,
  ward_id UUID NOT NULL REFERENCES wards(id),
  date DATE,
  complaint_count INT DEFAULT 0,
  resolved_count INT DEFAULT 0,
  avg_resolution_time_hours FLOAT,
  cleanliness_score FLOAT CHECK (cleanliness_score BETWEEN 0 AND 100),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(ward_id, date)
);
```

### Technology Choices

| Layer | Tool | Reasoning |
|-------|------|-----------|
| **Backend Framework** | FastAPI | Async, fast, excellent for async image processing + real-time updates |
| **Database** | PostgreSQL + PostGIS | PostGIS for spatial queries (radius search, clustering) |
| **Cache** | Redis | In-memory cache for dashboard metrics; task queue for image classification |
| **Task Queue** | Celery + Redis | Async image classification (don't block API) |
| **Image Processing** | Pillow + scikit-image | Compression, EXIF stripping, SSIM comparison |
| **AI/ML** | OpenAI Vision API | No model training; use pre-built for waste classification |
| **Clustering** | scikit-learn (DBSCAN) | Hotspot detection in batch job (weekly) |
| **Frontend** | React 18 + Vite | Fast build, PWA support, Tailwind CSS |
| **PWA** | Workbox | Offline support, background sync |
| **Maps** | Leaflet + OpenStreetMap | Lightweight, self-hosted tiles (no Google API costs) |
| **Image Storage** | AWS S3 | Scalable, cheap, CDN-ready |
| **Deployment** | Docker + Railway/Render | Single-dev-friendly, easy scaling |
| **Auth** | JWT + httponly cookies | Stateless, secure for PWA |

---

## 7. Data Model & Workflows

### Complaint Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│ OPEN                                                    │
│ - Citizen submitted report                              │
│ - AI classification pending (async)                     │
└────────────────┬────────────────────────────────────────┘
                 │ (Auto-assign after 5 sec)
┌────────────────▼────────────────────────────────────────┐
│ ASSIGNED                                                │
│ - Officer receives notification                         │
│ - Officer can accept or reassign                        │
└────────────────┬────────────────────────────────────────┘
                 │ (Officer clicks "start work")
┌────────────────▼────────────────────────────────────────┐
│ IN_PROGRESS                                             │
│ - Crew is at location                                   │
│ - Timer starts for SLA tracking                         │
└────────────────┬────────────────────────────────────────┘
                 │ (Pickup completed, photo uploaded)
┌────────────────▼────────────────────────────────────────┐
│ RESOLVED                                                │
│ - Before/after photo SSIM verified                      │
│ - Citizen notified                                      │
│ - Complaint archived                                    │
└─────────────────────────────────────────────────────────┘

FAILURE PATHS:
- OPEN → REJECTED (officer: duplicate or false report)
- IN_PROGRESS → ESCALATED (overdue > 48 hrs → senior officer)
```

### Hotspot Detection (Weekly Batch)

```python
# Pseudo-code: Runs every Sunday 2 AM IST

complaints_7d = fetch_complaints(created_at > NOW() - 7 DAYS)
points = [(c.lat, c.lon) for c in complaints_7d]

# DBSCAN: eps=100m (~0.0009 degrees), min_samples=3
clusters = DBSCAN(eps=0.0009, min_samples=3).fit(points)

for cluster_id, members in clusters.items():
    hotspot = {
        'centroid': centroid(members),
        'incident_count': len(members),
        'status': 'active' if len(members) >= 5 else 'observed'
    }
    upsert_hotspot(hotspot)

# Auto-escalate chronic hotspots
for hotspot in hotspots(status='active', first_reported < 30 DAYS AGO):
    escalate_to_senior_officer(hotspot)
```

---

## 8. API Specification (FastAPI Routes)

### Authentication
```
POST /api/auth/register
  body: { email, phone, password, user_type, ward_id? }
  response: { access_token, user }

POST /api/auth/login
  body: { email, password }
  response: { access_token, user }

POST /api/auth/logout
  response: { success: true }
```

### Complaints
```
POST /api/complaints
  headers: { Authorization: Bearer <token> }
  body: { location, description, photo_file }
  response: { complaint_id, ticket_number, status, ward_id }

GET /api/complaints/<id>
  response: { complaint_id, status, created_at, resolved_at, images, assignment }

GET /api/complaints?ward_id=<id>&status=open&limit=50
  response: [ { complaint_id, location, severity_score, created_at } ]

PATCH /api/complaints/<id>
  body: { status, notes }
  response: { updated_at, status }
```

### Assignments
```
GET /api/assignments?assigned_to=<officer_id>&status=pending
  response: [ { assignment_id, complaint_id, due_at, priority } ]

PATCH /api/assignments/<id>
  body: { status, completion_image_url? }
  response: { status, verified, verification_ssim_score }
```

### Hotspots
```
GET /api/hotspots?ward_id=<id>
  response: [ { hotspot_id, centroid, incident_count, status, complaints: [...] } ]
```

### Metrics
```
GET /api/metrics/wards?date=2024-01-15
  response: [ { ward_id, complaint_count, resolved_count, cleanliness_score } ]

GET /api/metrics/wards/<id>/history?days=30
  response: [ { date, complaint_count, avg_resolution_time_hours } ]
```

---

## 9. User Interface Wireframes

### Citizen App: Report Page
```
┌────────────────────────────────┐
│ CleanLoop                      │ (header)
├────────────────────────────────┤
│                                │
│  📷 Take Photo / Upload        │ (big button)
│                                │
├────────────────────────────────┤
│ 📍 Location: [Auto-filled GPS] │ (allow edit)
│ 🏠 Address: [Manual entry]     │
├────────────────────────────────┤
│ Waste Type:  [Dropdown]        │
│ ⭐ Severity: [1-5 slider]      │
├────────────────────────────────┤
│ 📝 Description (optional):     │
│ [text area]                    │
├────────────────────────────────┤
│ [Submit] [Cancel]              │
└────────────────────────────────┘
```

### Officer Dashboard: Task List
```
┌────────────────────────────────────────┐
│ Officer Portal                         │
├────────────────────────────────────────┤
│ 🔴 5 Open Tasks | ⚠️ 2 Overdue         │
├────────────────────────────────────────┤
│ Task #123 [HIGH]     📍 Mylapore       │
│ Overflowing bin      ⏱️ Assigned 2h ago │
│ [View] [Accept]                        │
│                                        │
│ Task #121 [MEDIUM]   📍 T. Nagar       │
│ Illegal dumping      ⏱️ Assigned 8h ago │
│ [View] [Accept]                        │
│                                        │
│ Task #119 [LOW]      📍 Royapettah     │
│ Construction debris  ⏱️ Assigned 20h ago│
│ [View] [Accept]                        │
├────────────────────────────────────────┤
│ Filter: [Open] [Assigned] [In Progress]│
└────────────────────────────────────────┘
```

### Public Dashboard: Ward Rankings
```
┌────────────────────────────────────────┐
│ CleanLoop Dashboard                    │
├────────────────────────────────────────┤
│ 📍 Map View                            │
│  ╔══════════════════════════════════╗  │
│  ║  [Ward map with color overlay]  ║  │
│  ║  🟢 Green = Clean                ║  │
│  ║  🟡 Yellow = Moderate            ║  │
│  ║  🔴 Red = Needs Attention        ║  │
│  ╚══════════════════════════════════╝  │
├────────────────────────────────────────┤
│ 📊 Ward Rankings (Last 30 Days)       │
│ 1. Adyar        ✅ 92% resolved       │
│ 2. Teynampet    ✅ 88% resolved       │
│ 3. Mylapore     ⚠️  72% resolved      │
│ 4. T. Nagar     ❌ 60% resolved       │
├────────────────────────────────────────┤
│ [View Details] [Compare Wards]         │
└────────────────────────────────────────┘
```

---

## 10. Success Metrics (MVP)

### Operational Metrics
| Metric | Target | How Measured |
|--------|--------|--------------|
| **Citizen Adoption** | 500+ active users in pilot ward | App login count |
| **Report Volume** | 100+ complaints/week | Complaints table count |
| **Resolution Rate** | ≥80% within 48 hrs | (resolved_count / total) per SLA |
| **Avg Response Time** | <24 hrs (from open to assigned) | timestamp delta |
| **Hotspot Detection** | Identify 3–5 chronic problem areas | DBSCAN cluster count |

### Technical Metrics
| Metric | Target | How Measured |
|--------|--------|--------------|
| **API Response Time** | <500ms p95 | APM (Application Performance Monitoring) |
| **Image Classification Accuracy** | ≥80% (on manual validation set) | Confusion matrix |
| **Uptime** | ≥99% | Ping monitoring |
| **Mobile App Offline Sync** | ≥95% success rate | Sync error logs |

### User Satisfaction
| Metric | Target | How Measured |
|--------|--------|--------------|
| **Officer Adoption** | ≥2/2 ward officers using dashboard daily | Login frequency |
| **Citizen Satisfaction** | ≥4/5 stars on resolution experience | Post-resolution survey |
| **Report Accuracy** | ≥85% citizen confirmation of AI classification | Validation clicks |

---

## 11. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Solo Dev Overload** | Delays in Phase 2 | Prioritize ruthlessly; cut gamification if needed |
| **AI Misclassification** | Officers distrust system | Start with human-in-the-loop; officer confirms AI classification |
| **Officer Adoption Failure** | Dashboard sits unused | Weekly sync with pilot officers; iterate UI based on feedback |
| **GPS Accuracy in Urban Canyon** | Reports show wrong location | Allow manual address entry; fallback to geocoding API |
| **Image Storage Costs** | S3 bill unexpectedly high | Compress images to <1MB; delete old images after 2 years |
| **Database Performance** | Slow hotspot clustering | Test DBSCAN on 10K+ complaints; add PostGIS spatial index |

---

## 12. Out of Scope (Phase 2+)

These features are **NOT** included in the 6-month MVP:

- ❌ Contractor mobile app (route optimization, crew GPS tracking)
- ❌ Predictive hotspot forecasting (ML time-series model)
- ❌ SMS/WhatsApp notifications (email only for MVP)
- ❌ Integration with municipal ticketing systems (IMIS)
- ❌ Gamification (badges, leaderboards)
- ❌ Multi-language support (English only)
- ❌ Advanced analytics (trend reports, forecasting)

---

## 13. Deployment & Infrastructure

### Development Environment
```bash
# Local stack
docker-compose up  # PostgreSQL, Redis, S3 mock (LocalStack)
python -m uvicorn main:app --reload
npm run dev  # React frontend on http://localhost:3000
```

### Production Deployment
```
Architecture: Docker containers on Railway or Render

├── Backend (FastAPI)
│   ├── PostgreSQL (managed)
│   ├── Redis (managed)
│   └── Celery workers (image classification)
├── Frontend (React + PWA)
│   └── Vercel or Netlify
└── Storage
    └── AWS S3 (Chennai region for latency)
```

### CI/CD Pipeline
```
GitHub Workflows:
1. On PR: lint (flake8), test (pytest), build Docker image
2. On merge to main: deploy to staging
3. Manual approval: promote to production
```

---

## 14. Launch Plan

### Week 1–2: Stakeholder Alignment
- [ ] Secure partnership with 1 ward (Chennai Corporation)
- [ ] Get ward officer contact (2 officers for pilot)
- [ ] Collect ward boundary GeoJSON for map
- [ ] Set SLA expectations (response time, resolution target)

### Week 3–4: Citizen Recruitment
- [ ] Recruit 50–100 citizen testers (local WhatsApp groups, NGOs)
- [ ] Create onboarding video (2 min, Tamil subtitles)
- [ ] Set up help email/phone for support

### Week 5–8: Soft Beta
- [ ] Monitor metrics daily
- [ ] Weekly sync with officers (iterate dashboard)
- [ ] Fix critical bugs within 24 hrs

### Week 9: Scale to 3–5 Wards
- [ ] Add more wards to pilot
- [ ] Refine metrics calculation
- [ ] Publish first dashboard results (public announcement)

### Week 10+: Monitor & Iterate
- [ ] Track KPIs vs. targets
- [ ] Plan Phase 2 features based on user feedback

---

## 15. Approval & Sign-Off

**Product Owner**: [Your Name]  
**Tech Lead**: [Your Name] (solo dev)  
**Sponsor**: [Ward Officer / Municipal Contact]  
**Date**: [Today's Date]  

---

**Questions?** Tag specific sections in the PRD or request clarification on any flow, tech choice, or timeline.
