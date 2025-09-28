"""
Telemedicine Schemas
Pydantic schemas for telemedicine API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TelemedicineSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TelemedicineConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"


# Base schemas
class TelemedicineSessionBase(BaseModel):
    appointment_id: Optional[int] = None
    doctor_id: int
    patient_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    recording_enabled: bool = False
    consent_required: bool = True
    chat_enabled: bool = True
    screen_sharing_enabled: bool = True
    file_sharing_enabled: bool = True


class TelemedicineSessionCreate(TelemedicineSessionBase):
    pass


class TelemedicineSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    recording_enabled: Optional[bool] = None
    consent_required: Optional[bool] = None
    chat_enabled: Optional[bool] = None
    screen_sharing_enabled: Optional[bool] = None
    file_sharing_enabled: Optional[bool] = None


class TelemedicineSession(TelemedicineSessionBase):
    id: int
    tenant_id: int
    session_id: str
    status: TelemedicineSessionStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    room_url: Optional[str] = None
    room_token: Optional[str] = None
    max_participants: int
    recording_url: Optional[str] = None
    recording_duration: Optional[int] = None
    consent_granted: bool
    consent_granted_at: Optional[datetime] = None
    consent_expires_at: Optional[datetime] = None
    connection_quality: Optional[str] = None
    technical_issues: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TelemedicineMessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = "text"
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None


class TelemedicineMessageCreate(TelemedicineMessageBase):
    pass


class TelemedicineMessage(TelemedicineMessageBase):
    id: int
    session_id: int
    sender_id: int
    sender_type: str
    is_encrypted: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TelemedicineFileBase(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str
    file_size: int
    file_type: str
    mime_type: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False
    access_expires_at: Optional[datetime] = None


class TelemedicineFileCreate(TelemedicineFileBase):
    pass


class TelemedicineFile(TelemedicineFileBase):
    id: int
    session_id: int
    uploaded_by: int
    is_encrypted: bool
    encryption_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TelemedicineConsentBase(BaseModel):
    consent_type: str = Field(..., min_length=1, max_length=50)
    consent_text: str = Field(..., min_length=1)
    consent_version: str = Field(..., min_length=1, max_length=20)
    expires_at: Optional[datetime] = None


class TelemedicineConsentCreate(TelemedicineConsentBase):
    pass


class TelemedicineConsentUpdate(BaseModel):
    granted: Optional[bool] = None
    granted_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TelemedicineConsent(TelemedicineConsentBase):
    id: int
    session_id: int
    patient_id: int
    status: TelemedicineConsentStatus
    granted: Optional[bool] = None
    granted_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TelemedicineConfigurationBase(BaseModel):
    is_enabled: bool = True
    platform_name: str = "Prontivus Telemedicina"
    max_session_duration: int = 60
    max_participants_per_session: int = 4
    video_quality_default: str = "auto"
    recording_enabled: bool = True
    recording_retention_days: int = 30
    recording_consent_required: bool = True
    encryption_enabled: bool = True
    session_timeout_minutes: int = 15
    consent_required: bool = True
    consent_text_template: Optional[str] = None
    consent_expiration_hours: int = 24
    chat_enabled: bool = True
    screen_sharing_enabled: bool = True
    file_sharing_enabled: bool = True
    waiting_room_enabled: bool = True
    auto_create_sessions: bool = False
    integrate_with_calendar: bool = True
    notify_on_session_start: bool = True
    notify_on_session_end: bool = True
    notify_on_technical_issues: bool = True
    settings: Optional[Dict[str, Any]] = None


class TelemedicineConfigurationCreate(TelemedicineConfigurationBase):
    pass


class TelemedicineConfigurationUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    platform_name: Optional[str] = None
    max_session_duration: Optional[int] = None
    max_participants_per_session: Optional[int] = None
    video_quality_default: Optional[str] = None
    recording_enabled: Optional[bool] = None
    recording_retention_days: Optional[int] = None
    recording_consent_required: Optional[bool] = None
    encryption_enabled: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    consent_required: Optional[bool] = None
    consent_text_template: Optional[str] = None
    consent_expiration_hours: Optional[int] = None
    chat_enabled: Optional[bool] = None
    screen_sharing_enabled: Optional[bool] = None
    file_sharing_enabled: Optional[bool] = None
    waiting_room_enabled: Optional[bool] = None
    auto_create_sessions: Optional[bool] = None
    integrate_with_calendar: Optional[bool] = None
    notify_on_session_start: Optional[bool] = None
    notify_on_session_end: Optional[bool] = None
    notify_on_technical_issues: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class TelemedicineConfiguration(TelemedicineConfigurationBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Specialized schemas for API responses
class TelemedicineSessionJoin(BaseModel):
    """Schema for joining a telemedicine session"""
    session_id: str
    participant_type: str = Field(..., regex="^(doctor|patient)$")
    participant_id: int


class TelemedicineSessionJoinResponse(BaseModel):
    """Response when joining a session"""
    success: bool
    room_url: str
    room_token: str
    session_status: str
    message: Optional[str] = None


class TelemedicineSessionStart(BaseModel):
    """Schema for starting a session"""
    session_id: str
    start_recording: bool = False


class TelemedicineSessionEnd(BaseModel):
    """Schema for ending a session"""
    session_id: str
    reason: Optional[str] = None
    notes: Optional[str] = None


class TelemedicineConsentRequest(BaseModel):
    """Schema for requesting patient consent"""
    session_id: str
    consent_type: str
    consent_text: str
    expires_in_hours: int = 24


class TelemedicineConsentResponse(BaseModel):
    """Schema for patient consent response"""
    consent_id: int
    granted: bool
    granted_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# Analytics schemas
class TelemedicineAnalyticsBase(BaseModel):
    duration_minutes: Optional[int] = None
    participants_count: Optional[int] = None
    messages_count: Optional[int] = None
    files_shared_count: Optional[int] = None
    average_connection_quality: Optional[str] = None
    technical_issues_count: int = 0
    reconnections_count: int = 0
    patient_active_time_minutes: Optional[int] = None
    doctor_active_time_minutes: Optional[int] = None
    recording_duration_minutes: Optional[int] = None
    recording_file_size_mb: Optional[int] = None
    patient_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    doctor_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)


class TelemedicineAnalyticsCreate(TelemedicineAnalyticsBase):
    pass


class TelemedicineAnalytics(TelemedicineAnalyticsBase):
    id: int
    tenant_id: int
    session_id: int
    patient_join_time: Optional[datetime] = None
    patient_leave_time: Optional[datetime] = None
    doctor_join_time: Optional[datetime] = None
    doctor_leave_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard and summary schemas
class TelemedicineDashboardResponse(BaseModel):
    """Dashboard response with telemedicine statistics"""
    total_sessions: int
    active_sessions: int
    completed_sessions_today: int
    average_session_duration: float
    patient_satisfaction_average: float
    technical_issues_today: int
    upcoming_sessions: int
    recording_storage_used_mb: int


class TelemedicineSessionSummary(BaseModel):
    """Summary of a telemedicine session"""
    id: int
    session_id: str
    title: str
    doctor_name: str
    patient_name: str
    status: str
    scheduled_start: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    connection_quality: Optional[str] = None
    recording_enabled: bool
    consent_granted: bool


class TelemedicineSessionsResponse(BaseModel):
    """Response with list of telemedicine sessions"""
    sessions: List[TelemedicineSessionSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
