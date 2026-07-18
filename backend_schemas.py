import pydantic
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Auth Schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    user_type: str  # 'citizen', 'officer', 'admin'
    ward_id: Optional[UUID] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID


class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: Optional[str] = None
    user_type: str
    ward_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Complaint Schemas
class LocationRequest(BaseModel):
    """Request model for GPS location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ComplaintCreateRequest(BaseModel):
    """Request model for creating a complaint."""
    description: str = Field(..., min_length=1, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    waste_type: Optional[str] = None
    severity_score: Optional[int] = Field(default=3, ge=1, le=5)

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    """Response model for complaint details."""
    id: UUID
    ticket_number: str
    citizen_id: UUID
    ward_id: UUID
    status: str
    description: Optional[str] = None
    waste_type: Optional[str] = None
    severity_score: int = 3
    image_urls: Optional[List[str]] = []
    ai_waste_type: Optional[str] = None
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplaintUpdateRequest(BaseModel):
    """Request model for updating complaint status."""
    status: str = Field(..., pattern="^(open|assigned|in_progress|resolved|rejected)$")
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        from_attributes = True


# Assignment Schemas
class AssignmentResponse(BaseModel):
    """Response model for assignment details."""
    id: UUID
    complaint_id: UUID
    assigned_to: UUID
    status: str
    assigned_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified: bool = False
    completion_image_url: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AssignmentUpdateRequest(BaseModel):
    """Request model for updating assignment status."""
    status: str = Field(..., pattern="^(accepted|in_progress|completed|escalated)$")
    completion_image_url: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ComplaintWithAssignmentResponse(BaseModel):
    """Full complaint with linked assignment details."""
    id: UUID
    ticket_number: str
    citizen_id: UUID
    ward_id: UUID
    status: str
    description: Optional[str] = None
    waste_type: Optional[str] = None
    severity_score: int = 3
    image_urls: Optional[List[str]] = []
    ai_waste_type: Optional[str] = None
    ai_confidence: Optional[float] = None
    assignment: Optional[AssignmentResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Hotspot Schemas
class HotspotResponse(BaseModel):
    """Response model for hotspot details."""
    id: UUID
    ward_id: UUID
    incident_count: int
    status: str
    first_reported: Optional[datetime] = None
    last_reported: Optional[datetime] = None

    class Config:
        from_attributes = True


# Metrics Schemas
class WardMetricResponse(BaseModel):
    """Response model for ward metrics."""
    ward_id: UUID
    date: str
    complaint_count: int
    resolved_count: int
    avg_resolution_time_hours: Optional[float] = None
    cleanliness_score: Optional[float] = None

    class Config:
        from_attributes = True
