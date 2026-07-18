# CleanLoop Setup Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/cleanloop.git
cd cleanloop

# Copy environment template
cp .env.example .env

# Edit .env with your values (OpenAI API key, email credentials, etc.)
nano .env
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL, Redis, LocalStack S3 (Docker)
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Backend Setup

```bash
# Create Python virtual environment
python -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (when Alembic is set up)
# alembic upgrade head

# Start FastAPI server
python -m uvicorn backend_main:app --reload
# Server runs on http://localhost:8000
# API docs on http://localhost:8000/docs
```

### 4. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies (if package.json not in root)
npm install

# Start Vite dev server
npm run dev
# Frontend runs on http://localhost:3000
```

### 5. Verify Everything Works

- **Backend Health**: `curl http://localhost:8000/health`
- **Frontend**: Open `http://localhost:3000` in browser
- **API Docs**: Open `http://localhost:8000/docs` (Swagger UI)

---

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://cleanloop:cleanloop_dev@localhost:5432/cleanloop_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI API
OPENAI_API_KEY=sk-...

# AWS S3 (LocalStack for dev)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_S3_BUCKET=cleanloop-images
AWS_S3_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# App
APP_ENV=development
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## API Endpoints (MVP Scope)

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Complaints
- `POST /api/complaints` - Submit complaint (with photo)
- `GET /api/complaints/<id>` - Get complaint details
- `GET /api/complaints?ward_id=<id>&status=open` - List complaints
- `PATCH /api/complaints/<id>` - Update status

### Assignments (Officer Dashboard)
- `GET /api/assignments?assigned_to=<officer_id>&status=pending` - Get tasks
- `PATCH /api/assignments/<id>` - Update task status

### Hotspots
- `GET /api/hotspots?ward_id=<id>` - Get hotspots for ward

### Metrics (Public Dashboard)
- `GET /api/metrics/wards?date=2024-01-15` - Get ward metrics
- `GET /api/metrics/wards/<id>/history?days=30` - Get historical data

---

## Project Structure

See `PROJECT_STRUCTURE.md` for detailed folder layout.

Key directories:
- `backend_*.py` - Temporary file structure (move to `backend/app/` after organization)
- `frontend_*.tsx|json|css` - Temporary frontend files (move to `frontend/src/` after organization)

---

## Development Workflow

### Backend Development
1. Edit files in `backend/app/`
2. Run `python -m uvicorn backend_main:app --reload` for hot reload
3. Check API docs at `http://localhost:8000/docs`

### Frontend Development
1. Edit files in `frontend/src/`
2. Vite auto-refreshes browser on save
3. Open DevTools (F12) to debug

### Database Changes
1. Create model in `backend_models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Apply migration: `alembic upgrade head`

---

## Testing

### Run Backend Tests (when setup)
```bash
pytest tests/ -v
```

### Run Frontend Tests (when setup)
```bash
npm run test
```

---

## Deployment

### Build Docker Image
```bash
docker build -t cleanloop-backend:0.1.0 -f backend/Dockerfile .
```

### Deploy to Railway/Render
See deployment guides in `backend/Dockerfile` comments.

---

## Troubleshooting

### PostgreSQL Connection Error
```bash
# Check if DB is running
docker ps

# Restart containers
docker-compose down
docker-compose up -d
```

### Port Already in Use
```bash
# If port 8000 is taken:
python -m uvicorn backend_main:app --reload --port 8001

# If port 3000 is taken:
npm run dev -- --port 3001
```

### S3 LocalStack Issues
```bash
# Recreate S3 bucket:
aws s3 mb s3://cleanloop-images --endpoint-url http://localhost:4566 --region us-east-1
```

---

## Next Steps

1. **Phase 1 (Weeks 1-8)**
   - [ ] Set up database migrations with Alembic
   - [ ] Implement auth routes + JWT
   - [ ] Implement complaint CRUD + image upload
   - [ ] Integrate OpenAI Vision API
   - [ ] Build citizen report form UI

2. **Phase 2 (Weeks 9-16)**
   - [ ] Implement hotspot detection (DBSCAN)
   - [ ] Build officer dashboard
   - [ ] Build public cleanliness dashboard
   - [ ] Add metrics calculation

3. **Phase 3 (Weeks 17-24)**
   - [ ] Performance optimization
   - [ ] Privacy compliance
   - [ ] Launch preparation
   - [ ] Beta testing with 1 ward

---

**Questions?** Check `PRD.md` for detailed specifications or create a GitHub Issue.
