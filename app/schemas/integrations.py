from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class IntegrationType(str, Enum):
    HEALTH_PLAN = "health_plan"
    TELEMEDICINE = "telemedicine"
    EMR = "emr"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PHARMACY = "pharmacy"
    PAYMENT = "payment"

class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class HealthPlanType(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"

class TelemedicineProvider(str, Enum):
    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    WEBEX = "webex"
    CUSTOM = "custom"

# Health Plan Integration schemas
class HealthPlanIntegrationBase(BaseModel):
    integration_name: str = Field(..., min_length=1, max_length=200)
    health_plan_id: int
    integration_type: IntegrationType = IntegrationType.HEALTH_PLAN
    api_endpoint: str = Field(..., min_length=1, max_length=500)
    api_version: Optional[str] = Field(None, max_length=20)
    authentication_method: str = Field(..., min_length=1, max_length=50)
    client_id: Optional[str] = Field(None, max_length=200)
    client_secret: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    configuration: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    plan_code: Optional[str] = Field(None, max_length=100)
    plan_name: Optional[str] = Field(None, max_length=200)
    coverage_details: Optional[Dict[str, Any]] = None
    copayment_info: Optional[Dict[str, Any]] = None
    authorization_required: bool = True

class HealthPlanIntegrationCreate(HealthPlanIntegrationBase):
    pass

class HealthPlanIntegrationUpdate(BaseModel):
    integration_name: Optional[str] = Field(None, min_length=1, max_length=200)
    health_plan_id: Optional[int] = None
    integration_type: Optional[IntegrationType] = None
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    api_version: Optional[str] = Field(None, max_length=20)
    authentication_method: Optional[str] = Field(None, min_length=1, max_length=50)
    client_id: Optional[str] = Field(None, max_length=200)
    client_secret: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    configuration: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    plan_code: Optional[str] = Field(None, max_length=100)
    plan_name: Optional[str] = Field(None, max_length=200)
    coverage_details: Optional[Dict[str, Any]] = None
    copayment_info: Optional[Dict[str, Any]] = None
    authorization_required: Optional[bool] = None
    status: Optional[IntegrationStatus] = None

class HealthPlanIntegration(HealthPlanIntegrationBase):
    id: int
    status: IntegrationStatus
    last_sync: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Telemedicine Integration schemas
class TelemedicineIntegrationBase(BaseModel):
    integration_name: str = Field(..., min_length=1, max_length=200)
    provider: TelemedicineProvider
    api_endpoint: str = Field(..., min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    authentication_method: str = Field(..., min_length=1, max_length=50)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    configuration: Optional[Dict[str, Any]] = None
    default_settings: Optional[Dict[str, Any]] = None
    max_participants: int = Field(100, ge=1, le=1000)
    recording_enabled: bool = True
    waiting_room_enabled: bool = True
    breakout_rooms_enabled: bool = False

class TelemedicineIntegrationCreate(TelemedicineIntegrationBase):
    pass

class TelemedicineIntegrationUpdate(BaseModel):
    integration_name: Optional[str] = Field(None, min_length=1, max_length=200)
    provider: Optional[TelemedicineProvider] = None
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    authentication_method: Optional[str] = Field(None, min_length=1, max_length=50)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    configuration: Optional[Dict[str, Any]] = None
    default_settings: Optional[Dict[str, Any]] = None
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    recording_enabled: Optional[bool] = None
    waiting_room_enabled: Optional[bool] = None
    breakout_rooms_enabled: Optional[bool] = None
    status: Optional[IntegrationStatus] = None

class TelemedicineIntegration(TelemedicineIntegrationBase):
    id: int
    status: IntegrationStatus
    last_sync: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Telemedicine Session schemas
class TelemedicineSessionBase(BaseModel):
    integration_id: int
    appointment_id: Optional[int] = None
    patient_id: int
    doctor_id: int
    session_title: str = Field(..., min_length=1, max_length=200)
    session_description: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    provider_session_id: Optional[str] = Field(None, max_length=200)
    meeting_url: Optional[str] = Field(None, max_length=500)
    meeting_password: Optional[str] = Field(None, max_length=100)
    dial_in_numbers: Optional[Dict[str, Any]] = None
    status: str = Field("scheduled", max_length=50)
    participants: Optional[Dict[str, Any]] = None
    recording_url: Optional[str] = Field(None, max_length=500)
    transcript_url: Optional[str] = Field(None, max_length=500)
    session_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class TelemedicineSessionCreate(TelemedicineSessionBase):
    pass

class TelemedicineSessionUpdate(BaseModel):
    integration_id: Optional[int] = None
    appointment_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    session_title: Optional[str] = Field(None, min_length=1, max_length=200)
    session_description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    provider_session_id: Optional[str] = Field(None, max_length=200)
    meeting_url: Optional[str] = Field(None, max_length=500)
    meeting_password: Optional[str] = Field(None, max_length=100)
    dial_in_numbers: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=50)
    participants: Optional[Dict[str, Any]] = None
    recording_url: Optional[str] = Field(None, max_length=500)
    transcript_url: Optional[str] = Field(None, max_length=500)
    session_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class TelemedicineSession(TelemedicineSessionBase):
    id: int
    session_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Integration Sync Log schemas
class IntegrationSyncLogBase(BaseModel):
    integration_id: Optional[int] = None
    telemedicine_integration_id: Optional[int] = None
    sync_type: str = Field(..., min_length=1, max_length=50)
    sync_start: datetime
    sync_end: Optional[datetime] = None
    status: str = Field("running", max_length=50)
    records_processed: int = Field(0, ge=0)
    records_created: int = Field(0, ge=0)
    records_updated: int = Field(0, ge=0)
    records_failed: int = Field(0, ge=0)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    sync_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class IntegrationSyncLogCreate(IntegrationSyncLogBase):
    pass

class IntegrationSyncLog(IntegrationSyncLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Health Plan Authorization schemas
class HealthPlanAuthorizationBase(BaseModel):
    integration_id: int
    patient_id: int
    doctor_id: int
    procedure_id: Optional[int] = None
    procedure_code: str = Field(..., min_length=1, max_length=50)
    procedure_description: str = Field(..., min_length=1, max_length=500)
    requested_date: date
    urgency_level: str = Field("normal", max_length=20)
    request_data: Dict[str, Any]
    request_sent_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    response_received_at: Optional[datetime] = None
    authorization_status: str = Field("pending", max_length=50)
    authorized_amount: Optional[Decimal] = Field(None, ge=0)
    copayment_amount: Optional[Decimal] = Field(None, ge=0)
    authorization_valid_until: Optional[date] = None
    authorization_notes: Optional[str] = None
    status: str = Field("pending", max_length=50)
    error_message: Optional[str] = None

class HealthPlanAuthorizationCreate(HealthPlanAuthorizationBase):
    pass

class HealthPlanAuthorizationUpdate(BaseModel):
    integration_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    procedure_id: Optional[int] = None
    procedure_code: Optional[str] = Field(None, min_length=1, max_length=50)
    procedure_description: Optional[str] = Field(None, min_length=1, max_length=500)
    requested_date: Optional[date] = None
    urgency_level: Optional[str] = Field(None, max_length=20)
    request_data: Optional[Dict[str, Any]] = None
    request_sent_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    response_received_at: Optional[datetime] = None
    authorization_status: Optional[str] = Field(None, max_length=50)
    authorized_amount: Optional[Decimal] = Field(None, ge=0)
    copayment_amount: Optional[Decimal] = Field(None, ge=0)
    authorization_valid_until: Optional[date] = None
    authorization_notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None

class HealthPlanAuthorization(HealthPlanAuthorizationBase):
    id: int
    authorization_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Integration Webhook schemas
class IntegrationWebhookBase(BaseModel):
    webhook_name: str = Field(..., min_length=1, max_length=200)
    integration_id: Optional[int] = None
    telemedicine_integration_id: Optional[int] = None
    webhook_url: str = Field(..., min_length=1, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    events: List[str]
    authentication_method: str = Field("none", max_length=50)
    auth_username: Optional[str] = Field(None, max_length=100)
    auth_password: Optional[str] = Field(None, max_length=200)
    auth_token: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    retry_count: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(30, ge=5, le=300)

class IntegrationWebhookCreate(IntegrationWebhookBase):
    pass

class IntegrationWebhookUpdate(BaseModel):
    webhook_name: Optional[str] = Field(None, min_length=1, max_length=200)
    integration_id: Optional[int] = None
    telemedicine_integration_id: Optional[int] = None
    webhook_url: Optional[str] = Field(None, min_length=1, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=200)
    events: Optional[List[str]] = None
    authentication_method: Optional[str] = Field(None, max_length=50)
    auth_username: Optional[str] = Field(None, max_length=100)
    auth_password: Optional[str] = Field(None, max_length=200)
    auth_token: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)

class IntegrationWebhook(IntegrationWebhookBase):
    id: int
    last_triggered: Optional[datetime] = None
    success_count: int
    failure_count: int
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Webhook Log schemas
class WebhookLogBase(BaseModel):
    webhook_id: int
    request_url: str = Field(..., min_length=1, max_length=500)
    request_method: str = Field(..., min_length=1, max_length=10)
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, Any]] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = Field(0, ge=0)
    event_type: Optional[str] = Field(None, max_length=100)
    event_data: Optional[Dict[str, Any]] = None

class WebhookLogCreate(WebhookLogBase):
    pass

class WebhookLog(WebhookLogBase):
    id: int
    executed_at: datetime

    class Config:
        from_attributes = True

# Integration Health Check schemas
class IntegrationHealthCheckBase(BaseModel):
    integration_id: Optional[int] = None
    telemedicine_integration_id: Optional[int] = None
    check_type: str = Field(..., min_length=1, max_length=50)
    check_start: datetime
    check_end: Optional[datetime] = None
    status: str = Field(..., min_length=1, max_length=20)
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None

class IntegrationHealthCheckCreate(IntegrationHealthCheckBase):
    pass

class IntegrationHealthCheck(IntegrationHealthCheckBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Request/Response schemas
class IntegrationSearchRequest(BaseModel):
    integration_name: Optional[str] = None
    integration_type: Optional[IntegrationType] = None
    status: Optional[IntegrationStatus] = None
    provider: Optional[TelemedicineProvider] = None
    created_by: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class TelemedicineSessionSearchRequest(BaseModel):
    integration_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class AuthorizationSearchRequest(BaseModel):
    integration_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    authorization_status: Optional[str] = None
    procedure_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class IntegrationSyncRequest(BaseModel):
    integration_id: int
    sync_type: str = "data_sync"
    force_sync: bool = False

class TelemedicineSessionRequest(BaseModel):
    integration_id: int
    patient_id: int
    doctor_id: int
    session_title: str
    session_description: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    appointment_id: Optional[int] = None

class AuthorizationRequest(BaseModel):
    integration_id: int
    patient_id: int
    doctor_id: int
    procedure_code: str
    procedure_description: str
    requested_date: date
    urgency_level: str = "normal"
    procedure_id: Optional[int] = None

class IntegrationSummary(BaseModel):
    total_integrations: int
    active_integrations: int
    health_plan_integrations: int
    telemedicine_integrations: int
    integrations_by_status: Dict[str, int]
    integrations_by_type: Dict[str, int]
    total_sessions: int
    active_sessions: int
    total_authorizations: int
    pending_authorizations: int

class IntegrationAnalytics(BaseModel):
    total_integrations: int
    active_integrations: int
    failed_integrations: int
    integrations_by_provider: Dict[str, int]
    session_statistics: Dict[str, int]
    authorization_statistics: Dict[str, int]
    sync_statistics: Dict[str, int]
    webhook_statistics: Dict[str, int]
    health_check_results: Dict[str, int]
    performance_metrics: Dict[str, float]
