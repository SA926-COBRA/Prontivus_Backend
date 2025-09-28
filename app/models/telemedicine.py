"""
Telemedicine Models
Models for native telemedicine video platform
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class TelemedicineSessionStatus(str, enum.Enum):
    """Telemedicine session status"""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TelemedicineConsentStatus(str, enum.Enum):
    """Patient consent status"""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"


class TelemedicineSession(Base):
    """Telemedicine video session"""
    __tablename__ = "telemedicine_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Session details
    session_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique session identifier
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    
    # Participants
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Session information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Status and state
    status = Column(Enum(TelemedicineSessionStatus), default=TelemedicineSessionStatus.SCHEDULED)
    
    # Video room configuration
    room_url = Column(String(500), nullable=True)  # Unique room URL
    room_token = Column(Text, nullable=True)  # Encrypted room access token
    max_participants = Column(Integer, default=2)
    
    # Recording settings
    recording_enabled = Column(Boolean, default=False)
    recording_url = Column(String(500), nullable=True)
    recording_duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Consent management
    consent_required = Column(Boolean, default=True)
    consent_granted = Column(Boolean, default=False)
    consent_granted_at = Column(DateTime(timezone=True), nullable=True)
    consent_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional features
    chat_enabled = Column(Boolean, default=True)
    screen_sharing_enabled = Column(Boolean, default=True)
    file_sharing_enabled = Column(Boolean, default=True)
    
    # Technical details
    connection_quality = Column(String(20), nullable=True)  # poor, fair, good, excellent
    technical_issues = Column(JSON, nullable=True)  # Store technical issues encountered
    
    # Metadata
    session_metadata = Column(JSON, nullable=True)  # Additional session metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    appointment = relationship("Appointment")
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient")
    messages = relationship("TelemedicineMessage", back_populates="session")
    files = relationship("TelemedicineFile", back_populates="session")


class TelemedicineMessage(Base):
    """Chat messages during telemedicine sessions"""
    __tablename__ = "telemedicine_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("telemedicine_sessions.id"), nullable=False, index=True)
    
    # Message details
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_type = Column(String(20), nullable=False)  # doctor, patient, system
    message_type = Column(String(20), default="text")  # text, file, system
    
    # Content
    content = Column(Text, nullable=False)
    file_url = Column(String(500), nullable=True)  # For file messages
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Message state
    is_encrypted = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("TelemedicineSession", back_populates="messages")
    sender = relationship("User")


class TelemedicineFile(Base):
    """Files shared during telemedicine sessions"""
    __tablename__ = "telemedicine_files"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("telemedicine_sessions.id"), nullable=False, index=True)
    
    # File details
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_key = Column(String(255), nullable=True)  # Encrypted file encryption key
    
    # Access control
    is_public = Column(Boolean, default=False)  # Can be accessed by all session participants
    access_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # File tags for organization
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("TelemedicineSession", back_populates="files")
    uploader = relationship("User")


class TelemedicineConsent(Base):
    """Patient consent for telemedicine sessions"""
    __tablename__ = "telemedicine_consents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("telemedicine_sessions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Consent details
    consent_type = Column(String(50), nullable=False)  # video_session, recording, data_sharing
    status = Column(Enum(TelemedicineConsentStatus), default=TelemedicineConsentStatus.PENDING)
    
    # Consent content
    consent_text = Column(Text, nullable=False)
    consent_version = Column(String(20), nullable=False)  # Version of consent text
    
    # Patient response
    granted = Column(Boolean, nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IP address when consent was given
    user_agent = Column(Text, nullable=True)  # Browser/device info
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session = relationship("TelemedicineSession")
    patient = relationship("Patient")


class TelemedicineConfiguration(Base):
    """Global telemedicine configuration for tenants"""
    __tablename__ = "telemedicine_configuration"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Platform settings
    is_enabled = Column(Boolean, default=True)
    platform_name = Column(String(100), default="Prontivus Telemedicina")
    
    # Video settings
    max_session_duration = Column(Integer, default=60)  # Minutes
    max_participants_per_session = Column(Integer, default=4)
    video_quality_default = Column(String(20), default="auto")  # auto, low, medium, high
    
    # Recording settings
    recording_enabled = Column(Boolean, default=True)
    recording_retention_days = Column(Integer, default=30)
    recording_consent_required = Column(Boolean, default=True)
    
    # Security settings
    encryption_enabled = Column(Boolean, default=True)
    session_timeout_minutes = Column(Integer, default=15)  # Auto-disconnect after inactivity
    
    # Consent settings
    consent_required = Column(Boolean, default=True)
    consent_text_template = Column(Text, nullable=True)
    consent_expiration_hours = Column(Integer, default=24)
    
    # Feature toggles
    chat_enabled = Column(Boolean, default=True)
    screen_sharing_enabled = Column(Boolean, default=True)
    file_sharing_enabled = Column(Boolean, default=True)
    waiting_room_enabled = Column(Boolean, default=True)
    
    # Integration settings
    auto_create_sessions = Column(Boolean, default=False)  # Auto-create for appointments
    integrate_with_calendar = Column(Boolean, default=True)
    
    # Notification settings
    notify_on_session_start = Column(Boolean, default=True)
    notify_on_session_end = Column(Boolean, default=True)
    notify_on_technical_issues = Column(Boolean, default=True)
    
    # Additional configuration
    settings = Column(JSON, nullable=True)  # Platform-specific settings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")


class TelemedicineAnalytics(Base):
    """Analytics data for telemedicine sessions"""
    __tablename__ = "telemedicine_analytics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("telemedicine_sessions.id"), nullable=False, index=True)
    
    # Session metrics
    duration_minutes = Column(Integer, nullable=True)
    participants_count = Column(Integer, nullable=True)
    messages_count = Column(Integer, nullable=True)
    files_shared_count = Column(Integer, nullable=True)
    
    # Quality metrics
    average_connection_quality = Column(String(20), nullable=True)
    technical_issues_count = Column(Integer, default=0)
    reconnections_count = Column(Integer, default=0)
    
    # Patient engagement
    patient_join_time = Column(DateTime(timezone=True), nullable=True)
    patient_leave_time = Column(DateTime(timezone=True), nullable=True)
    patient_active_time_minutes = Column(Integer, nullable=True)
    
    # Doctor metrics
    doctor_join_time = Column(DateTime(timezone=True), nullable=True)
    doctor_leave_time = Column(DateTime(timezone=True), nullable=True)
    doctor_active_time_minutes = Column(Integer, nullable=True)
    
    # Recording metrics
    recording_duration_minutes = Column(Integer, nullable=True)
    recording_file_size_mb = Column(Integer, nullable=True)
    
    # Satisfaction metrics
    patient_satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    doctor_satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    session = relationship("TelemedicineSession")
