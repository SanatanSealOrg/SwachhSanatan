# Phase 1 Week 1-2 Authentication - Quick Reference

## File Locations (8 Files Created/Modified)

### New Files
```
backend/app/__init__.py                  (44 bytes)  - Package init
backend/app/config.py                    (664 bytes) - Configuration
backend/app/dependencies.py              (2,913 bytes) - Dependency injection
backend/app/services/__init__.py         (45 bytes)  - Services package
backend/app/services/auth_service.py     (6,621 bytes) - Auth logic
backend/app/api/__init__.py              (47 bytes)  - API package
backend/app/api/auth.py                  (6,540 bytes) - Auth routes
backend/init_db.py                       (1,200 bytes) - DB initialization
```

### Modified Files
```
backend_main.py                          (+2 lines) - Added auth router
backend_schemas.py                       (+17 lines) - Added UserResponse
```

## Quick Start

1. **Install dependencies** (if not done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY and DATABASE_URL
   ```

3. **Initialize database**:
   ```bash
   python backend/init_db.py
   ```
   Expected output:
   ```
   ✅ Database initialization completed successfully!
   Tables created:
     - users
     - wards
     - complaints
     - assignments
     - hotspots
     - ward_metrics
   ```

4. **Run the server**:
   ```bash
   python backend_main.py
   ```
   Server runs at http://0.0.0.0:8000

5. **Access API docs**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints (3 New)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/auth/register` | Create new user | No |
| POST | `/api/auth/login` | Get access token | No |
| GET | `/api/auth/me` | Get user profile | Yes (Bearer) |

## Request/Response Examples

### Register
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "phone": "9876543210",
    "password": "MySecurePass123",
    "user_type": "citizen"
  }'
```

Response (201):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "MySecurePass123"
  }'
```

Response (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

Response (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "email": "user@example.com",
  "phone": "9876543210",
  "user_type": "citizen",
  "ward_id": null,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

## Key Features

✅ **Security**
- Bcrypt password hashing
- JWT token authentication (HS256)
- Bearer token validation
- Email & phone uniqueness enforcement

✅ **Validation**
- Password strength (min 8 characters)
- Email format validation (Pydantic EmailStr)
- User type validation (citizen/officer/admin)
- Duplicate prevention

✅ **Error Handling**
- Proper HTTP status codes (201, 200, 400, 401, 500)
- Descriptive error messages
- Generic auth failure messages (security)
- Exception logging

✅ **Code Quality**
- Full type hints
- Comprehensive docstrings with examples
- Dependency injection pattern
- Separation of concerns (service/api/dependencies)
- All files lint-clean (LINT OK)

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    phone VARCHAR UNIQUE,
    password_hash VARCHAR NOT NULL,
    user_type ENUM('citizen', 'officer', 'admin') NOT NULL,
    ward_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError: No module named 'backend' | Add to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` |
| Database connection refused | Check PostgreSQL running, verify DATABASE_URL in .env |
| Token invalid on GET /auth/me | Token expires in 30 min, generate new token with login |
| CORS error from frontend | Update ALLOWED_ORIGINS in .env to match frontend URL |
| Password hashing slow | Expected! Bcrypt intentionally slow for security. Normal: 100-500ms |

## Performance Metrics (Expected)

| Operation | Time |
|-----------|------|
| Registration (with bcrypt) | 200-500ms |
| Login (with bcrypt verify) | 200-500ms |
| Get current user (DB query) | < 50ms |
| Token generation (JWT) | < 10ms |

## Testing Documentation

See `AUTHENTICATION_TESTING.md` for:
- 6 registration scenarios (valid, weak password, duplicates, invalid type)
- 3 login scenarios (valid, email not found, wrong password)
- 4 /me scenarios (valid token, missing header, malformed token, expired token)
- Complete user journey example
- Database verification queries
- Security features breakdown
- Troubleshooting guide

## Integration Checklist

- ✅ Database models (User, UserType enum) created
- ✅ Schemas (UserRegisterRequest, UserLoginRequest, TokenResponse) defined
- ✅ Config loaded from environment variables
- ✅ Auth service with bcrypt and JWT implemented
- ✅ Dependencies for DB session and current user created
- ✅ API endpoints (register, login, me) created
- ✅ Routes integrated into main FastAPI app
- ✅ Database initialization script ready
- ✅ Error handling with proper HTTP status codes
- ✅ Logging for security events
- ✅ All files linted and passing syntax checks
- ✅ Documentation complete

## Next Phase (Week 3)

Ready to implement:
- Complaint creation endpoints
- Assignment management
- Hotspot detection
- Dashboard metrics
- File upload (images)
- Notifications
