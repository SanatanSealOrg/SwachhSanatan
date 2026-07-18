# Complaint CRUD & Image Upload - Implementation Guide

## Phase 1 Week 3-4: Complete Complaint Management System

### Overview
This document covers the implementation of complaint creation, retrieval, filtering, and status management with integrated image upload, compression, EXIF stripping, and S3 storage.

---

## Files Created/Modified

### New Files Created

#### Services Layer
1. **backend/app/services/complaint_service.py**
   - `generate_ticket_number(complaint_id)` - Creates unique ticket ID
   - `find_ward_by_location(db, lat, lon)` - PostGIS geospatial query
   - `create_complaint(db, citizen_id, lat, lon, ...)` - Main complaint creation
   - `get_complaint_by_id(db, complaint_id)` - Retrieve single complaint
   - `list_complaints_by_ward(db, ward_id, status, limit)` - Paginated ward queries
   - `update_complaint_status(db, complaint_id, new_status, notes)` - Status changes
   - `get_complaint_count_by_ward(db, ward_id, status)` - Count for pagination

2. **backend/app/services/image_service.py**
   - `compress_image(image_bytes, max_width=1920, max_height=1920, quality=85)` - Pillow image optimization
   - `strip_exif_metadata(image_bytes)` - Privacy-safe metadata removal
   - `generate_thumbnail(image_bytes, size=(200, 200))` - Thumbnail generation
   - `upload_image_to_s3(file_bytes, filename, complaint_id, bucket)` - boto3 S3 upload

#### Utilities
3. **backend/app/utils/validators.py**
   - `validate_gps_coordinates(lat, lon)` - Latitude/longitude range checks
   - `validate_file_size(file_size, max_mb=5)` - File size validation
   - `validate_file_type(filename)` - Image type validation (jpg, jpeg, png, gif, webp)
   - `validate_waste_type(waste_type)` - Waste type enum validation
   - `validate_severity_score(severity_score)` - Score range 1-5 validation

4. **backend/app/utils/s3.py**
   - `get_s3_client()` - boto3 S3 client initialization (supports LocalStack)
   - `get_s3_key(complaint_id, filename)` - S3 key path generation

#### API Routes
5. **backend/app/api/complaints.py**
   - `POST /api/complaints` - Submit complaint with image
   - `GET /api/complaints/{complaint_id}` - Get complaint details
   - `GET /api/complaints?ward_id=X&status=Y` - List complaints (officer)
   - `PATCH /api/complaints/{complaint_id}` - Update status (officer only)

#### Package Stub
6. **backend/app/workers/__init__.py**
   - Celery workers package (ready for async task queue)

### Modified Files

1. **backend/app/dependencies.py**
   - Added `get_current_officer()` dependency - Verifies user_type == 'officer'

2. **backend_schemas.py**
   - Added `LocationRequest` - GPS coordinate validation
   - Enhanced `ComplaintCreateRequest` - Field validation and constraints
   - Enhanced `ComplaintResponse` - Added ai_waste_type, ai_confidence, updated_at
   - Added `ComplaintUpdateRequest` - Status update request model

3. **backend_main.py**
   - Imported complaints router
   - Registered complaints router at `/api` prefix

---

## API Endpoints

### 1. POST /api/complaints - Submit Complaint with Image

**Authentication**: Required (Bearer token)
**User Type**: Citizen, Officer, Admin
**Content-Type**: multipart/form-data

**Request Body**:
```
Form Data:
  - description (string, required): Complaint description (1-500 chars)
  - latitude (float, required): GPS latitude (-90 to 90)
  - longitude (float, required): GPS longitude (-180 to 180)
  - waste_type (string, optional): 'bin' | 'dumping' | 'construction' | 'biohazard'
  - severity_score (integer, optional): 1-5, default 3
  - file (file, required): Image file (.jpg, .jpeg, .png, .gif, .webp, max 5MB)
```

**Success Response (201 Created)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "ticket_number": "CL-1689234852-4567",
  "citizen_id": "123e4567-e89b-12d3-a456-426614174001",
  "ward_id": "123e4567-e89b-12d3-a456-426614174002",
  "status": "open",
  "description": "Overflowing waste bin at corner",
  "waste_type": "bin",
  "severity_score": 4,
  "image_urls": ["https://s3.../complaints/uuid/photo.jpg"],
  "ai_waste_type": null,
  "ai_confidence": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "resolved_at": null
}
```

**Error Responses**:
- 400: Invalid GPS coordinates, unsupported file type, file >5MB, weak validation
- 401: Missing/invalid token
- 500: Server error

**Image Processing Pipeline**:
1. Validate GPS coordinates (-90/90, -180/180)
2. Validate file type (supported image extensions)
3. Validate file size (<5MB)
4. Strip EXIF metadata (privacy)
5. Compress image (Pillow: max 1920x1920, quality 85)
6. Auto-detect ward via PostGIS ST_Within query
7. Create complaint record with status='open'
8. Upload compressed image to S3
9. Update complaint with S3 URL
10. Generate ticket number (CL-{timestamp}-{random})

---

### 2. GET /api/complaints/{complaint_id} - Get Complaint Details

**Authentication**: Required (Bearer token)
**User Type**: Any authenticated user
**Path Parameters**:
- `complaint_id` (UUID): Complaint ID

**Success Response (200 OK)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "ticket_number": "CL-1689234852-4567",
  "citizen_id": "123e4567-e89b-12d3-a456-426614174001",
  "ward_id": "123e4567-e89b-12d3-a456-426614174002",
  "status": "open",
  "description": "Overflowing waste bin at corner",
  "waste_type": "bin",
  "severity_score": 4,
  "image_urls": ["https://s3.../complaints/uuid/photo.jpg"],
  "ai_waste_type": null,
  "ai_confidence": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "resolved_at": null
}
```

**Error Responses**:
- 401: Missing/invalid token
- 404: Complaint not found
- 500: Server error

---

### 3. GET /api/complaints - List Complaints by Ward

**Authentication**: Required (Bearer token)
**User Type**: Officer (can only see their ward), Admin/Citizen (all wards)
**Query Parameters**:
- `ward_id` (UUID, required): Ward ID
- `status` (string, optional): 'open' | 'assigned' | 'in_progress' | 'resolved' | 'rejected'
- `limit` (integer, optional): 1-100, default 50
- `offset` (integer, optional): Pagination offset, default 0

**Success Response (200 OK)**:
```json
{
  "complaints": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "ticket_number": "CL-1689234852-4567",
      "citizen_id": "...",
      "ward_id": "...",
      "status": "open",
      "description": "...",
      "waste_type": "bin",
      "severity_score": 4,
      "image_urls": ["https://s3.../..."],
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00",
      "resolved_at": null
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Error Responses**:
- 400: Invalid status filter
- 401: Missing/invalid token
- 403: Officer accessing different ward
- 500: Server error

**Sorting**: By created_at DESC (newest first)

---

### 4. PATCH /api/complaints/{complaint_id} - Update Complaint Status

**Authentication**: Required (Bearer token)
**User Type**: Officer only (must belong to complaint's ward)
**Path Parameters**:
- `complaint_id` (UUID): Complaint ID

**Request Body**:
```json
{
  "status": "in_progress|resolved|rejected|assigned",
  "notes": "Optional notes about the update"
}
```

**Success Response (200 OK)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "ticket_number": "CL-1689234852-4567",
  "citizen_id": "...",
  "ward_id": "...",
  "status": "in_progress",
  "description": "...",
  "waste_type": "bin",
  "severity_score": 4,
  "image_urls": ["https://s3.../..."],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00",
  "resolved_at": null
}
```

**Error Responses**:
- 400: Invalid status value
- 401: Missing/invalid token, not an officer
- 403: Officer accessing different ward
- 404: Complaint not found
- 500: Server error

**Side Effects**:
- Status transitions validated (open → assigned → in_progress → resolved)
- `updated_at` timestamp updated automatically
- If status='resolved', `resolved_at` timestamp set to current time
- Audit trail via notes field

---

## Database Schema Integration

### Complaint Model (backend_models.py)
```python
class Complaint:
  id: UUID (PK)
  ticket_number: str (unique, indexed)
  citizen_id: UUID (FK User)
  ward_id: UUID (FK Ward)
  location: POINT (PostGIS geometry, SRID 4326)
  waste_type: Enum (bin|dumping|construction|biohazard)
  severity_score: int (1-5, default 3)
  description: text
  image_urls: ARRAY(String)
  status: Enum (open|assigned|in_progress|resolved|rejected)
  created_at: timestamp (indexed)
  updated_at: timestamp
  resolved_at: timestamp (nullable)
  ai_waste_type: string (for ML predictions)
  ai_confidence: float (0-1)
  hotspot_id: UUID (FK Hotspot, nullable)
```

### PostGIS Queries
- `ST_Within(point, ward_geometry)` - Determine ward from GPS coordinates
- Supports complex polygon geometries for ward boundaries
- SRID 4326 (WGS 84 - standard GPS)

---

## Image Processing Pipeline

### Input
- File: jpg, jpeg, png, gif, webp (max 5MB)
- Image size: any

### Processing Steps
1. **EXIF Stripping** (Privacy)
   - Remove location metadata
   - Remove camera info
   - Remove timestamps
   - Tool: PIL Image serialization

2. **Compression** (Efficiency)
   - Resize to max 1920x1920 (maintains aspect ratio)
   - JPEG quality: 85 (good balance)
   - Convert RGBA → RGB if needed
   - Target: <2MB output

3. **Thumbnail Generation** (UI)
   - Size: 200x200
   - Format: JPEG, quality 85
   - Used for preview in listings

### S3 Upload
- Endpoint: AWS S3 or LocalStack (dev)
- Bucket: `cleanloop-complaints` (configurable)
- Key: `complaints/{complaint_id}/{filename}`
- Content-Type: `image/jpeg`
- Returns: Full S3 URL for storage

---

## Error Handling

### Validation Errors
```python
# GPS Coordinates
validate_gps_coordinates(13.0827, 80.2707)
# Returns: (True, "") or (False, "Latitude must be between -90 and 90")

# File Size
validate_file_size(5242880, max_mb=5)
# Returns: (True, "") or (False, "File size must not exceed 5 MB")

# File Type
validate_file_type("photo.jpg")
# Returns: (True, "") or (False, "File type must be one of: gif, jpeg, jpg, png, webp")

# Waste Type
validate_waste_type("bin")
# Returns: (True, "") or (False, "Waste type must be one of: bin, construction, dumping, biohazard")

# Severity Score
validate_severity_score(4)
# Returns: (True, "") or (False, "Severity score must be between 1 and 5")
```

### Business Logic Errors
- Ward not found: "Could not determine ward for given location"
- Image processing: "Failed to compress image: ..."
- S3 upload: "Failed to upload image to S3: ..."
- Officer ward mismatch: "You can only update complaints from your assigned ward"

---

## Configuration & Environment Variables

### Required
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/cleanloop_db
SECRET_KEY=your-secret-key-change-in-production
```

### S3/LocalStack
```env
# Production (AWS S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=cleanloop-complaints

# Development (LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
S3_BUCKET=cleanloop-complaints
```

### Optional
```env
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Testing Checklist

### Manual Testing with cURL

#### 1. Create Complaint
```bash
# First, register and login to get token
TOKEN="your-jwt-token"

# Create complaint with image
curl -X POST http://localhost:8000/api/complaints \
  -H "Authorization: Bearer $TOKEN" \
  -F "description=Overflowing waste bin at corner" \
  -F "latitude=13.0827" \
  -F "longitude=80.2707" \
  -F "waste_type=bin" \
  -F "severity_score=4" \
  -F "file=@/path/to/photo.jpg"

# Expected: 201 Created with complaint details
```

#### 2. Get Complaint
```bash
curl -X GET http://localhost:8000/api/complaints/{complaint_id} \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with complaint details
```

#### 3. List Complaints
```bash
curl -X GET "http://localhost:8000/api/complaints?ward_id={ward_id}&status=open&limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with paginated complaints array
```

#### 4. Update Status (Officer)
```bash
# Login as officer
OFFICER_TOKEN="officer-jwt-token"

curl -X PATCH http://localhost:8000/api/complaints/{complaint_id} \
  -H "Authorization: Bearer $OFFICER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "notes": "Cleaning crew assigned"
  }'

# Expected: 200 OK with updated complaint
```

### API Documentation (Swagger)
```
Navigate to: http://localhost:8000/docs
- See all endpoints with request/response schemas
- Try endpoints with "Try it out" button
- Test with real data
```

### Validation Tests
```python
# In test file:
from backend.app.utils.validators import validate_gps_coordinates, validate_file_size

# Test GPS validation
assert validate_gps_coordinates(13.0827, 80.2707) == (True, "")
assert validate_gps_coordinates(91, 0)[0] == False

# Test file size validation
assert validate_file_size(1024 * 1024 * 3) == (True, "")
assert validate_file_size(1024 * 1024 * 10)[0] == False
```

---

## PostGIS Integration

### Setup
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create spatial index on wards
CREATE INDEX idx_wards_geometry ON wards USING GIST (geometry);
```

### Query Example
```python
# In complaint_service.py
from geoalchemy2 import func

# Find ward for location (13.0827, 80.2707)
point = "POINT(80.2707 13.0827)"  # Note: lon, lat (X, Y)
ward = db.query(Ward).filter(
    func.ST_Within(
        func.ST_GeomFromText(point, 4326),
        Ward.geometry
    )
).first()
```

---

## Security Considerations

1. **EXIF Metadata**: Stripped before storage (prevents location tracking)
2. **File Type Validation**: Only images accepted
3. **File Size Limit**: 5MB max to prevent abuse
4. **Officer Authorization**: Only officers can update; must belong to ward
5. **JWT Token**: Required for all endpoints
6. **GPS Validation**: Prevents invalid coordinates
7. **S3 Bucket**: Private by default; configure ACLs as needed

---

## Performance Optimizations

1. **Image Compression**: <2MB target reduces storage/bandwidth
2. **Thumbnail Generation**: Optional for UI performance
3. **DB Indexing**: ticket_number, status, created_at indexed
4. **PostGIS Spatial Index**: GIST index on ward geometries
5. **Pagination**: limit/offset for large result sets
6. **Lazy Loading**: Images loaded on-demand from S3

---

## Monitoring & Logging

### Log Messages
- "Image compressed: XXX.XXkB → XXX.XXkB" - Compression success
- "EXIF metadata stripped from image" - Privacy-safe processing
- "Image uploaded to S3: complaints/uuid/filename" - Upload success
- "Complaint created: CL-... (citizen: uuid)" - Creation audit
- "Complaint {id} not found for status update" - Not found warning
- "Officer {id} attempted to access ward {id}" - Security audit

### Metrics to Track
- Complaints per ward (trending)
- Average resolution time (SLA)
- Image upload success rate
- S3 upload latency
- API response times

---

## Next Steps (Phase 2)

1. **AI Integration** (Waste classification)
   - Call ML model to auto-detect waste_type
   - Set ai_waste_type and ai_confidence

2. **Hotspot Detection**
   - Aggregate complaints by geography
   - Identify chronic problem areas

3. **Assignment System**
   - Create assignments from complaints
   - Track completion

4. **Notifications**
   - Email/SMS alerts to officers
   - Citizen updates on complaint status

5. **Analytics Dashboard**
   - Ward metrics and trends
   - Officer performance tracking

---

## Files Summary

| File | Purpose | Status |
|------|---------|--------|
| backend/app/services/complaint_service.py | Business logic | ✅ Created |
| backend/app/services/image_service.py | Image processing | ✅ Created |
| backend/app/api/complaints.py | API endpoints | ✅ Created |
| backend/app/utils/validators.py | Input validation | ✅ Created |
| backend/app/utils/s3.py | S3 integration | ✅ Created |
| backend/app/workers/__init__.py | Celery stub | ✅ Created |
| backend/app/dependencies.py | Officer dependency | ✅ Updated |
| backend_schemas.py | Pydantic models | ✅ Updated |
| backend_main.py | Router registration | ✅ Updated |

---

## Success Criteria - All Met ✅

- ✅ POST /api/complaints accepts multipart file upload
- ✅ GPS validation (-90/90, -180/180)
- ✅ Image compression & EXIF stripping
- ✅ S3 upload with LocalStack support
- ✅ PostGIS ward detection (ST_Within)
- ✅ Ticket number generation
- ✅ GET /api/complaints/{id} returns full details
- ✅ GET /api/complaints?ward_id=X&status=Y lists paginated complaints
- ✅ PATCH /api/complaints/{id} updates status (officer only)
- ✅ File type & size validation
- ✅ Officer authorization checks
- ✅ Error handling with descriptive messages
- ✅ Pydantic schema validation
- ✅ All Python files lint OK

---

## Support

For issues:
1. Check error response message
2. Verify environment variables set
3. Review logs in docker-compose or terminal
4. Test with Swagger UI at /docs
5. Check S3 bucket configuration

