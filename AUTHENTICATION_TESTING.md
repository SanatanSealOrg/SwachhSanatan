"""
Authentication API Testing Guide

This document provides comprehensive examples for testing the Phase 1 Week 1-2 
authentication implementation using FastAPI's built-in Swagger UI at http://localhost:8000/docs
"""

# ============================================================================
# QUICK START: Running the Application
# ============================================================================

"""
1. Install dependencies:
   pip install -r requirements.txt

2. Create .env file from .env.example:
   cp .env.example .env
   
   Update the following in .env:
   SECRET_KEY=your-secret-key-change-in-production
   DATABASE_URL=postgresql://cleanloop:cleanloop_dev@localhost:5432/cleanloop_db

3. Initialize database:
   python backend/init_db.py
   
   Output:
   🚀 Starting database initialization...
   ✅ Database initialization completed successfully!
   Tables created:
     - users
     - wards
     - complaints
     - assignments
     - hotspots
     - ward_metrics

4. Start the API server:
   python backend_main.py
   
   Output:
   INFO:     Application startup complete
   Uvicorn running on http://0.0.0.0:8000
   
5. Access the Swagger UI:
   Navigate to http://localhost:8000/docs
   
   All 3 auth endpoints are listed:
   - POST /api/auth/register
   - POST /api/auth/login
   - GET /api/auth/me
"""

# ============================================================================
# TEST 1: User Registration
# ============================================================================

"""
Endpoint: POST /api/auth/register
Expected Response: 201 CREATED

Scenario 1a: Valid registration as citizen
"""

request_body_1a = {
    "email": "citizen@example.com",
    "phone": "9876543210",
    "password": "SecurePass123",
    "user_type": "citizen",
    "ward_id": None
}

expected_response_1a = {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user_id": "123e4567-e89b-12d3-a456-426614174001"
}

"""
Test Steps:
1. Click "Try it out" on POST /api/auth/register in Swagger UI
2. Copy request_body_1a into the request body
3. Click "Execute"
4. Expected status: 201
5. Response includes access_token (JWT), token_type, and user_id
6. Save the access_token for testing GET /api/auth/me

Database verification:
  SELECT email, user_type, is_active FROM users 
  WHERE email = 'citizen@example.com';
  
  Result:
  email             | user_type | is_active
  citizen@example.com | citizen   | true
"""


"""
Scenario 1b: Valid registration as officer with ward_id
"""

request_body_1b = {
    "email": "officer@ward1.com",
    "phone": "9876543211",
    "password": "OfficerPass456",
    "user_type": "officer",
    "ward_id": "123e4567-e89b-12d3-a456-426614174000"
}

expected_response_1b = {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user_id": "123e4567-e89b-12d3-a456-426614174002"
}

"""
Test Steps:
1. Click "Try it out" on POST /api/auth/register
2. Copy request_body_1b into the request body
3. Click "Execute"
4. Expected status: 201
5. Verify ward_id is stored in response

Database verification:
  SELECT email, user_type, ward_id FROM users 
  WHERE email = 'officer@ward1.com';
"""


"""
Scenario 1c: Invalid - Password too weak (< 8 chars)
"""

request_body_1c = {
    "email": "weak@example.com",
    "phone": "9876543212",
    "password": "weak",
    "user_type": "citizen"
}

expected_response_1c = {
    "detail": "Password must be at least 8 characters long"
}

"""
Test Steps:
1. Click "Try it out" on POST /api/auth/register
2. Copy request_body_1c into the request body
3. Click "Execute"
4. Expected status: 400 (Bad Request)
5. Response detail matches expected message
"""


"""
Scenario 1d: Invalid - Duplicate email
"""

request_body_1d = {
    "email": "citizen@example.com",  # Same as Scenario 1a
    "phone": "9999999999",
    "password": "DifferentPass789",
    "user_type": "citizen"
}

expected_response_1d = {
    "detail": "Email citizen@example.com already registered"
}

"""
Test Steps:
1. First ensure Scenario 1a registration succeeded
2. Click "Try it out" on POST /api/auth/register
3. Copy request_body_1d into the request body
4. Click "Execute"
5. Expected status: 400 (Bad Request)
6. Response detail includes "already registered"
"""


"""
Scenario 1e: Invalid - Duplicate phone
"""

request_body_1e = {
    "email": "different@example.com",
    "phone": "9876543210",  # Same as Scenario 1a
    "password": "DifferentPass789",
    "user_type": "citizen"
}

expected_response_1e = {
    "detail": "Phone 9876543210 already registered"
}

"""
Test Steps:
1. First ensure Scenario 1a registration succeeded
2. Click "Try it out" on POST /api/auth/register
3. Copy request_body_1e into the request body
4. Click "Execute"
5. Expected status: 400 (Bad Request)
6. Response detail includes "already registered"
"""


"""
Scenario 1f: Invalid - Invalid user_type
"""

request_body_1f = {
    "email": "invalid@example.com",
    "phone": "9999888888",
    "password": "ValidPass123",
    "user_type": "superuser"  # Invalid type
}

expected_response_1f = {
    "detail": "Invalid user_type. Must be one of: citizen, officer, admin"
}

"""
Test Steps:
1. Click "Try it out" on POST /api/auth/register
2. Copy request_body_1f into the request body
3. Click "Execute"
4. Expected status: 400 (Bad Request)
5. Response detail lists valid user types
"""


# ============================================================================
# TEST 2: User Login
# ============================================================================

"""
Endpoint: POST /api/auth/login
Expected Response: 200 OK

Scenario 2a: Valid login with correct email/password
"""

request_body_2a = {
    "email": "citizen@example.com",
    "password": "SecurePass123"
}

expected_response_2a = {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user_id": "123e4567-e89b-12d3-a456-426614174001"
}

"""
Test Steps:
1. First ensure Scenario 1a registration succeeded (citizen@example.com)
2. Click "Try it out" on POST /api/auth/login
3. Copy request_body_2a into the request body
4. Click "Execute"
5. Expected status: 200
6. Response includes different access_token (new JWT) from registration
7. token_type is "bearer"
8. user_id matches registered user
9. Save the access_token for testing GET /api/auth/me
"""


"""
Scenario 2b: Invalid - Email not found
"""

request_body_2b = {
    "email": "nonexistent@example.com",
    "password": "AnyPassword123"
}

expected_response_2b = {
    "detail": "Invalid email or password"
}

"""
Test Steps:
1. Click "Try it out" on POST /api/auth/login
2. Copy request_body_2b into the request body
3. Click "Execute"
4. Expected status: 401 (Unauthorized)
5. Response detail is "Invalid email or password" (no hint which is wrong)
"""


"""
Scenario 2c: Invalid - Correct email, wrong password
"""

request_body_2c = {
    "email": "citizen@example.com",
    "password": "WrongPassword123"
}

expected_response_2c = {
    "detail": "Invalid email or password"
}

"""
Test Steps:
1. First ensure Scenario 1a registration succeeded
2. Click "Try it out" on POST /api/auth/login
3. Copy request_body_2c into the request body
4. Click "Execute"
5. Expected status: 401 (Unauthorized)
6. Response detail is same generic message (security best practice)
"""


# ============================================================================
# TEST 3: Get Current User
# ============================================================================

"""
Endpoint: GET /api/auth/me
Expected Response: 200 OK (with valid token), 401 Unauthorized (without/invalid token)

Scenario 3a: Valid - Authenticated request with valid JWT
"""

request_headers_3a = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

expected_response_3a = {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "email": "citizen@example.com",
    "phone": "9876543210",
    "user_type": "citizen",
    "ward_id": None,
    "is_active": True,
    "created_at": "2024-01-15T10:30:00"
}

"""
Test Steps:
1. Complete Scenario 2a (POST /api/auth/login) to get valid access_token
2. Copy the access_token value
3. Click "Try it out" on GET /api/auth/me
4. Click "Authorize" button (lock icon, top right of Swagger UI)
5. Paste the access_token into the "value" field
6. Click "Authorize" and then "Close"
7. Click "Execute" on GET /api/auth/me
8. Expected status: 200
9. Response includes user details without password_hash
10. All fields match the registered user
"""


"""
Scenario 3b: Invalid - Missing Authorization header
"""

request_headers_3b = {
    # No Authorization header
}

expected_response_3b = {
    "detail": "Not authenticated"
}

"""
Test Steps:
1. Click "Try it out" on GET /api/auth/me
2. Do NOT add Authorization header
3. Click "Execute"
4. Expected status: 403 (Forbidden) or 401 (Unauthorized)
5. Response indicates missing credentials
"""


"""
Scenario 3c: Invalid - Malformed Bearer token
"""

request_headers_3c = {
    "Authorization": "Bearer invalid.token.here"
}

expected_response_3c = {
    "detail": "Invalid authentication credentials"
}

"""
Test Steps:
1. Click "Authorize" button in Swagger UI
2. Clear the value field and enter: Bearer invalid.token.here
3. Click "Authorize" and then "Close"
4. Click "Execute" on GET /api/auth/me
5. Expected status: 401 (Unauthorized)
6. Response indicates invalid token
"""


"""
Scenario 3d: Invalid - Expired token (if token expiration < current time)
"""

request_headers_3d = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." # Expired token
}

expected_response_3d = {
    "detail": "Invalid authentication credentials"
}

"""
Test Steps:
1. Create a token with past expiration using verify_token() function
2. Use that token in Authorization header
3. Expected status: 401 (Unauthorized)
4. Response indicates invalid/expired token

Note: Default token expiration is 30 minutes (from .env ACCESS_TOKEN_EXPIRE_MINUTES)
"""


# ============================================================================
# AUTHENTICATION FLOW - COMPLETE USER JOURNEY
# ============================================================================

"""
Complete User Journey (Citizen)
================================

1. REGISTER
   POST /api/auth/register
   Body: {
     "email": "newcitizen@example.com",
     "phone": "9123456789",
     "password": "MySecurePass123",
     "user_type": "citizen"
   }
   Response 201: { "access_token": "...", "token_type": "bearer", "user_id": "..." }
   
2. LOGIN (get fresh token)
   POST /api/auth/login
   Body: {
     "email": "newcitizen@example.com",
     "password": "MySecurePass123"
   }
   Response 200: { "access_token": "...", "token_type": "bearer", "user_id": "..." }
   
3. GET PROFILE
   GET /api/auth/me
   Headers: Authorization: Bearer <access_token>
   Response 200: {
     "id": "...",
     "email": "newcitizen@example.com",
     "phone": "9123456789",
     "user_type": "citizen",
     "ward_id": null,
     "is_active": true,
     "created_at": "..."
   }

Expected Flow Result:
- User can register with email/phone
- User can login and receive JWT token
- User can retrieve their profile using JWT
- All passwords are hashed (never stored in plain text)
- Duplicate emails/phones are rejected
- Invalid tokens are rejected
"""


# ============================================================================
# DATABASE VERIFICATION
# ============================================================================

"""
SQL queries to verify authentication implementation:

1. Count registered users:
   SELECT COUNT(*) FROM users;
   
2. Verify password hashing (passwords should be hashed, not plain text):
   SELECT email, LENGTH(password_hash) as hash_length FROM users;
   -- Expected hash_length: 60+ characters (bcrypt hash)
   
3. List all users with their types:
   SELECT id, email, phone, user_type, is_active, created_at FROM users;
   
4. Verify unique constraints:
   SELECT COUNT(*) FROM users WHERE email = 'test@example.com';
   -- Should be 0 or 1 (unique constraint enforced)
   
5. Check user creation time:
   SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 5;
   -- Shows 5 most recently created users
"""


# ============================================================================
# PERFORMANCE TESTING (Optional)
# ============================================================================

"""
Performance Considerations:

1. Password hashing (bcrypt):
   - Intentionally slow to prevent brute-force attacks
   - Registration and login may take 100-500ms
   - This is EXPECTED and DESIRED behavior

2. JWT token generation:
   - Very fast (< 10ms)
   - No database queries required
   
3. GET /api/auth/me:
   - 1 database query to fetch user
   - Should complete in < 50ms
   
Expected timing:
   POST /auth/register: 200-500ms (bcrypt hashing)
   POST /auth/login: 200-500ms (bcrypt verification)
   GET /auth/me: < 50ms (DB query only)
"""


# ============================================================================
# SECURITY FEATURES IMPLEMENTED
# ============================================================================

"""
✅ Security Features:

1. Password Security:
   - Bcrypt hashing with default cost factor
   - Never stored or logged in plain text
   - Hashed passwords are 60 characters (Blowfish hash)

2. JWT Tokens:
   - HS256 algorithm (HMAC with SHA-256)
   - Configurable expiration (default 30 minutes)
   - Secret key required from environment

3. Email Validation:
   - Pydantic EmailStr validator
   - Rejects invalid email formats

4. Duplicate Prevention:
   - Unique constraints on email and phone
   - Database-enforced at schema level
   - Application-level validation with error messages

5. Error Handling:
   - Generic error messages ("Invalid email or password")
   - No user enumeration attacks
   - Proper HTTP status codes (400, 401, 500)

6. CORS:
   - Configured in backend_main.py
   - Allows frontend to access auth endpoints

7. Dependency Injection:
   - Type-safe database sessions
   - JWT verification in dependencies
   - No sensitive data in logs
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Issue: "ModuleNotFoundError: No module named 'backend'"

Solution:
  - Ensure PYTHONPATH includes the project root
  - Run: export PYTHONPATH="${PYTHONPATH}:$(pwd)"
  - Then run: python backend_main.py

---

Issue: "Database connection refused"

Solution:
  - Verify PostgreSQL is running
  - Check DATABASE_URL in .env
  - Try: python backend/init_db.py
  - Check logs for specific connection error

---

Issue: "Token invalid" on GET /auth/me

Solution:
  - Ensure token was copied correctly
  - Remove "Bearer " prefix - Swagger UI adds it automatically
  - Token expires after 30 minutes (configurable in .env)
  - Generate new token with POST /auth/login

---

Issue: "CORS error" from frontend

Solution:
  - Check ALLOWED_ORIGINS in .env
  - For development: ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
  - Ensure frontend URL matches exactly (protocol, host, port)

---

Issue: "Password hashing takes too long"

Solution:
  - This is EXPECTED (bcrypt is intentionally slow)
  - Typical time: 100-500ms per request
  - This is GOOD for security
  - Don't try to speed it up
"""
