from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, Float, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from geoalchemy2 import Geometry
from datetime import datetime
import uuid
import enum
from backend_database import Base

# Enums
class UserType(str, enum.Enum):
    citizen = "citizen"
    officer = "officer"
    admin = "admin"

class ComplaintStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"

class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    escalated = "escalated"

class HotspotStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    chronic = "chronic"

class WasteType(str, enum.Enum):
    bin = "bin"
    dumping = "dumping"
    construction = "construction"
    biohazard = "biohazard"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ward(Base):
    __tablename__ = "wards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    ward_number = Column(Integer, nullable=True)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=True)
    population = Column(Integer, nullable=True)
    primary_officer_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    citizen_id = Column(UUID(as_uuid=True), nullable=False)
    ward_id = Column(UUID(as_uuid=True), nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    waste_type = Column(Enum(WasteType), nullable=True)
    severity_score = Column(Integer, nullable=False, default=3)
    description = Column(Text, nullable=True)
    image_urls = Column(ARRAY(String), nullable=True)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.open, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # AI metadata
    ai_waste_type = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    hotspot_id = Column(UUID(as_uuid=True), nullable=True)

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.pending, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_image_url = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    verification_ssim_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

class Hotspot(Base):
    __tablename__ = "hotspots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=False)
    centroid = Column(Geometry('POINT', srid=4326), nullable=False)
    incident_count = Column(Integer, default=0)
    first_reported = Column(DateTime, nullable=True)
    last_reported = Column(DateTime, nullable=True)
    status = Column(Enum(HotspotStatus), default=HotspotStatus.active)
    severity_trend = Column(String, nullable=True)  # 'increasing', 'stable', 'decreasing'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WardMetric(Base):
    __tablename__ = "ward_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    complaint_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    avg_resolution_time_hours = Column(Float, nullable=True)
    cleanliness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
