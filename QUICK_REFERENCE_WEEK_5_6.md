## Phase 1 Week 5-6 Quick Reference Guide

### 🎯 What's New

**3 New API Endpoints**
- `GET /api/assignments` — Officer task list
- `GET /api/assignments/{id}` — Assignment details
- `PATCH /api/assignments/{id}` — Update assignment status

**AI Image Classification**
- Automatic waste classification on complaint submission
- OpenAI GPT-4 Vision integration
- Confidence scoring

**Auto Officer Assignment**
- Complaints automatically assigned to available officers
- Load-balanced distribution
- 24-hour due date

---

## 🔧 Configuration

### Environment Variables Required

```bash
# OpenAI API
OPENAI_API_KEY=sk-xxx...

# Existing variables still needed
DATABASE_URL=postgresql://...
SECRET_KEY=...
ALGORITHM=HS256
```

---

## 📝 File Locations

| Feature | File |
|---------|------|
| AI Classification | `backend/app/services/ai_service.py` |
| Officer Assignment | `backend/app/services/assignment_service.py` |
| Assignment API | `backend/app/api/assignments.py` |
| Async Tasks | `backend/app/workers/celery_tasks.py` |

---

## 🔌 Integration Points

### Complaint Creation Flow
```python
# In backend/app/services/complaint_service.py
def create_complaint(...):
    # 1. Create complaint
    complaint = Complaint(...)
    db.add(complaint)
    db.commit()
    
    # 2. ✨ NEW: Classify image
    classification = ai_service.classify_image_with_openai(image_url)
    ai_service.update_complaint_with_classification(db, complaint.id, classification)
    
    # 3. ✨ NEW: Assign to officer
    assignment_service.auto_assign_complaint(db, complaint.id)
    
    return complaint
```

### Response Example
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ticket_number": "CL-1705316400000",
  "status": "assigned",
  "ai_waste_type": "bin",
  "ai_confidence": 0.92,
  "image_urls": ["https://s3.../image.jpg"],
  "citizen_id": "...",
  "ward_id": "..."
}
```

---

## 🎭 API Usage Examples

### Example 1: List Officer Assignments
```bash
curl -X GET \
  "http://localhost:8000/api/assignments?officer_id=<uuid>&status=pending" \
  -H "Authorization: Bearer <token>"
```

### Example 2: Get Assignment Details
```bash
curl -X GET \
  "http://localhost:8000/api/assignments/<assignment-uuid>" \
  -H "Authorization: Bearer <token>"
```

### Example 3: Accept Assignment
```bash
curl -X PATCH \
  "http://localhost:8000/api/assignments/<assignment-uuid>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "accepted",
    "notes": "Assignment acknowledged"
  }'
```

### Example 4: Mark as In Progress
```bash
curl -X PATCH \
  "http://localhost:8000/api/assignments/<assignment-uuid>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "notes": "Cleaning crew arrived"
  }'
```

### Example 5: Mark as Completed
```bash
curl -X PATCH \
  "http://localhost:8000/api/assignments/<assignment-uuid>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "completion_image_url": "https://s3.../after-image.jpg",
    "notes": "Waste removed, area cleaned"
  }'
```

---

## 🔒 Access Control

### Who Can Do What

| Action | Citizen | Officer | Admin |
|--------|---------|---------|-------|
| View own assignments | ❌ | ✅ (own only) | ✅ (any) |
| Update assignment status | ❌ | ✅ (own only) | ✅ |
| Create complaints | ✅ | ✅ | ✅ |
| View complaints | ✅ (own) | ✅ (assigned) | ✅ (any) |

---

## 📊 Status Transitions

```
Assignment Lifecycle:
pending → accepted → in_progress → completed
         ↘ escalated ↙
```

**Valid Transitions:**
- pending → accepted ✅
- pending → escalated ✅
- accepted → in_progress ✅
- accepted → escalated ✅
- in_progress → completed ✅
- in_progress → escalated ✅
- completed → (terminal) ❌
- escalated → (terminal) ❌

---

## 🔍 Debugging Tips

### Check Complaint Status
```python
# In Python shell
from backend_models import Complaint
complaint = db.query(Complaint).filter(Complaint.ticket_number == "CL-...").first()
print(f"Status: {complaint.status}")
print(f"AI Type: {complaint.ai_waste_type}")
print(f"AI Confidence: {complaint.ai_confidence}")
```

### Check Assignment
```python
from backend_models import Assignment
assignment = db.query(Assignment).filter(
    Assignment.complaint_id == complaint_id
).first()
print(f"Assigned to: {assignment.assigned_to}")
print(f"Status: {assignment.status}")
print(f"Due: {assignment.due_at}")
```

### Check OpenAI Integration
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key configured: {bool(api_key)}")
print(f"API Key starts with: {api_key[:10]}..." if api_key else "NOT SET")
```

### Monitor Logs
```bash
# Watch API logs
tail -f logs/cleanloop-api.log | grep -E "classification|assignment|ERROR"
```

---

## 🚨 Common Issues & Solutions

### Issue: "OPENAI_API_KEY not configured"
**Solution**: Set OPENAI_API_KEY in .env file
```bash
echo "OPENAI_API_KEY=sk-xxx..." >> .env
```

### Issue: "No available officers found in ward"
**Solution**: Ensure officers are created with correct ward_id
```sql
SELECT id, user_type, ward_id FROM users WHERE user_type='officer';
```

### Issue: Assignment not appearing after complaint creation
**Solution**: Check complaint service logs for errors
```bash
grep -i "auto.assign\|assignment" logs/cleanloop-api.log
```

### Issue: AI classification returning confidence 0
**Solution**: Check OpenAI API connectivity and rate limits
```bash
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

---

## 📚 Code Locations

**To Add Feature X...**

| Feature | File | Function |
|---------|------|----------|
| Change AI prompt | `ai_service.py` | `classify_image_with_openai()` line 48 |
| Adjust load balancing | `assignment_service.py` | `find_available_officer()` line 36 |
| Add validation to API | `assignments.py` | `update_assignment()` line 185 |
| Modify integration | `complaint_service.py` | `create_complaint()` line 171 |

---

## 🧪 Test Cases

### Test 1: Create Complaint (E2E)
```
1. POST /auth/register (citizen)
2. POST /auth/login (get token)
3. POST /complaints (with image)
4. GET /complaints/{id}
✅ Assert: status="assigned", ai_waste_type not null
```

### Test 2: Officer Workflow
```
1. POST /auth/register (officer in ward)
2. POST /auth/login (get token)
3. GET /assignments (should see complaint from Test 1)
4. PATCH /assignments/{id} (status: "in_progress")
5. GET /assignments/{id}
✅ Assert: status="in_progress"
```

### Test 3: Access Control
```
1. Officer A tries: GET /assignments?officer_id=<Officer B>
✅ Assert: 403 Forbidden
```

### Test 4: Invalid Transition
```
1. GET /assignments/{id} (status: "pending")
2. PATCH with status: "completed" (skip in_progress)
✅ Assert: 400 Bad Request
```

---

## 📈 Monitoring

### Key Metrics to Track
- Complaints created per hour
- Assignment success rate
- Average classification confidence
- Officer utilization rate
- Assignment completion time

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database
psql $DATABASE_URL -c "SELECT 1"

# OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models | head
```

---

## 📞 Support

**Questions?** Check:
1. `PHASE_1_WEEK_5_6_VERIFICATION.md` — Complete technical details
2. `PHASE_1_WEEK_5_6_COMPLETE.md` — Implementation summary
3. File docstrings — Function-level documentation
4. API docstrings — Endpoint details

---

**Last Updated**: Phase 1 Week 5-6 Implementation
**Status**: ✅ Production Ready
