"""
Health Plan Integration Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"


class AuthMethod(str, Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"


# Health Plan Provider Schemas
class HealthPlanProviderBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    cnpj: Optional[str] = Field(None, max_length=18)
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    base_url: str = Field(..., max_length=500)
    auth_method: AuthMethod = AuthMethod.OAUTH2
    api_version: str = Field(default="v1", max_length=20)
    
    # OAuth Configuration
    client_id: Optional[str] = Field(None, max_length=200)
    client_secret: Optional[str] = Field(None, max_length=500)
    scope: Optional[str] = Field(None, max_length=500)
    audience: Optional[str] = Field(None, max_length=500)
    authorization_url: Optional[str] = Field(None, max_length=500)
    token_url: Optional[str] = Field(None, max_length=500)
    
    # API Key Configuration
    api_key: Optional[str] = Field(None, max_length=500)
    api_key_header: str = Field(default="X-API-Key", max_length=100)
    
    # Basic Auth Configuration
    username: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, max_length=500)
    
    # Bearer Token Configuration
    bearer_token: Optional[str] = Field(None, max_length=500)
    
    # Additional Configuration
    additional_config: Optional[Dict[str, Any]] = None
    requires_doctor_id: bool = False
    supports_authorization: bool = True
    supports_eligibility: bool = True
    supports_sadt: bool = True
    
    # Status and Monitoring
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    connection_timeout: int = Field(default=30, ge=5, le=300)


class HealthPlanProviderCreate(HealthPlanProviderBase):
    pass


class HealthPlanProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    cnpj: Optional[str] = Field(None, max_length=18)
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    base_url: Optional[str] = Field(None, max_length=500)
    auth_method: Optional[AuthMethod] = None
    api_version: Optional[str] = Field(None, max_length=20)
    
    # OAuth Configuration
    client_id: Optional[str] = Field(None, max_length=200)
    client_secret: Optional[str] = Field(None, max_length=500)
    scope: Optional[str] = Field(None, max_length=500)
    audience: Optional[str] = Field(None, max_length=500)
    authorization_url: Optional[str] = Field(None, max_length=500)
    token_url: Optional[str] = Field(None, max_length=500)
    
    # API Key Configuration
    api_key: Optional[str] = Field(None, max_length=500)
    api_key_header: Optional[str] = Field(None, max_length=100)
    
    # Basic Auth Configuration
    username: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, max_length=500)
    
    # Bearer Token Configuration
    bearer_token: Optional[str] = Field(None, max_length=500)
    
    # Additional Configuration
    additional_config: Optional[Dict[str, Any]] = None
    requires_doctor_id: Optional[bool] = None
    supports_authorization: Optional[bool] = None
    supports_eligibility: Optional[bool] = None
    supports_sadt: Optional[bool] = None
    
    # Status and Monitoring
    status: Optional[IntegrationStatus] = None
    connection_timeout: Optional[int] = Field(None, ge=5, le=300)


class HealthPlanProviderInDB(HealthPlanProviderBase):
    id: int
    last_connection_test: Optional[datetime] = None
    last_connection_status: Optional[str] = None
    last_error_message: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


# API Endpoint Schemas
class HealthPlanAPIEndpointBase(BaseModel):
    provider_id: int
    name: str = Field(..., max_length=200)
    endpoint_type: str = Field(..., max_length=50)
    url: str = Field(..., max_length=500)
    method: str = Field(default="POST", max_length=10)
    headers: Optional[Dict[str, str]] = None
    request_format: str = Field(default="json", max_length=50)
    response_format: str = Field(default="json", max_length=50)
    requires_auth: bool = True
    auth_type: Optional[str] = Field(None, max_length=50)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=100000)


class HealthPlanAPIEndpointCreate(HealthPlanAPIEndpointBase):
    pass


class HealthPlanAPIEndpointUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    endpoint_type: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    headers: Optional[Dict[str, str]] = None
    request_format: Optional[str] = Field(None, max_length=50)
    response_format: Optional[str] = Field(None, max_length=50)
    requires_auth: Optional[bool] = None
    auth_type: Optional[str] = Field(None, max_length=50)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)


class HealthPlanAPIEndpointInDB(HealthPlanAPIEndpointBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Authorization Schemas
class HealthPlanAuthorizationBase(BaseModel):
    provider_id: int
    patient_id: int
    doctor_id: int
    procedure_code: str = Field(..., max_length=50)
    procedure_description: Optional[str] = Field(None, max_length=500)
    requested_date: datetime
    requested_quantity: int = Field(default=1, ge=1)
    
    # Patient Information
    patient_cpf: str = Field(..., max_length=14)
    patient_name: str = Field(..., max_length=200)
    patient_dob: Optional[datetime] = None
    patient_phone: Optional[str] = Field(None, max_length=20)
    
    # Doctor Information
    doctor_crm: str = Field(..., max_length=20)
    doctor_name: str = Field(..., max_length=200)
    
    # Clinical Information
    clinical_indication: str
    clinical_question: Optional[str] = None
    urgency_level: str = Field(default="routine", max_length=20)


class HealthPlanAuthorizationCreate(HealthPlanAuthorizationBase):
    pass


class HealthPlanAuthorizationUpdate(BaseModel):
    procedure_description: Optional[str] = Field(None, max_length=500)
    requested_quantity: Optional[int] = Field(None, ge=1)
    patient_phone: Optional[str] = Field(None, max_length=20)
    clinical_indication: Optional[str] = None
    clinical_question: Optional[str] = None
    urgency_level: Optional[str] = Field(None, max_length=20)


class HealthPlanAuthorizationInDB(HealthPlanAuthorizationBase):
    id: int
    authorization_number: str
    status: str = "pending"
    authorization_code: Optional[str] = None
    approval_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    denial_reason: Optional[str] = None
    api_request_id: Optional[str] = None
    api_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Eligibility Schemas
class HealthPlanEligibilityBase(BaseModel):
    provider_id: int
    patient_id: int
    patient_cpf: str = Field(..., max_length=14)
    patient_name: str = Field(..., max_length=200)
    patient_dob: Optional[datetime] = None
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_name: Optional[str] = Field(None, max_length=200)
    plan_type: Optional[str] = Field(None, max_length=100)


class HealthPlanEligibilityCreate(HealthPlanEligibilityBase):
    pass


class HealthPlanEligibilityUpdate(BaseModel):
    plan_number: Optional[str] = Field(None, max_length=100)
    plan_name: Optional[str] = Field(None, max_length=200)
    plan_type: Optional[str] = Field(None, max_length=100)


class HealthPlanEligibilityInDB(HealthPlanEligibilityBase):
    id: int
    eligibility_number: str
    verification_date: datetime
    is_eligible: Optional[bool] = None
    eligibility_status: Optional[str] = None
    coverage_start_date: Optional[datetime] = None
    coverage_end_date: Optional[datetime] = None
    coverage_details: Optional[Dict[str, Any]] = None
    copay_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    api_request_id: Optional[str] = None
    api_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Connection Log Schemas
class HealthPlanConnectionLogBase(BaseModel):
    provider_id: int
    endpoint_id: Optional[int] = None
    request_url: str = Field(..., max_length=500)
    request_method: str = Field(..., max_length=10)
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    response_status_code: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = Field(None, max_length=100)
    user_id: Optional[int] = None
    patient_id: Optional[int] = None
    request_type: Optional[str] = Field(None, max_length=50)


class HealthPlanConnectionLogCreate(HealthPlanConnectionLogBase):
    pass


class HealthPlanConnectionLogInDB(HealthPlanConnectionLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Configuration Schemas
class HealthPlanConfigurationBase(BaseModel):
    tenant_id: int
    default_timeout: int = Field(default=30, ge=5, le=300)
    max_retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)
    log_all_requests: bool = True
    log_response_bodies: bool = False
    log_retention_days: int = Field(default=90, ge=1, le=365)
    encrypt_sensitive_data: bool = True
    mask_logs: bool = True
    notify_on_errors: bool = True
    notify_on_slow_requests: bool = True
    slow_request_threshold_ms: int = Field(default=5000, ge=1000, le=30000)


class HealthPlanConfigurationCreate(HealthPlanConfigurationBase):
    pass


class HealthPlanConfigurationUpdate(BaseModel):
    default_timeout: Optional[int] = Field(None, ge=5, le=300)
    max_retry_attempts: Optional[int] = Field(None, ge=1, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=1, le=60)
    log_all_requests: Optional[bool] = None
    log_response_bodies: Optional[bool] = None
    log_retention_days: Optional[int] = Field(None, ge=1, le=365)
    encrypt_sensitive_data: Optional[bool] = None
    mask_logs: Optional[bool] = None
    notify_on_errors: Optional[bool] = None
    notify_on_slow_requests: Optional[bool] = None
    slow_request_threshold_ms: Optional[int] = Field(None, ge=1000, le=30000)


class HealthPlanConfigurationInDB(HealthPlanConfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Connection Schemas
class ConnectionTestRequest(BaseModel):
    provider_id: int
    endpoint_type: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


# Dashboard Schemas
class HealthPlanDashboardData(BaseModel):
    total_providers: int
    active_providers: int
    inactive_providers: int
    error_providers: int
    total_requests_today: int
    successful_requests_today: int
    failed_requests_today: int
    average_response_time_ms: float
    recent_errors: List[Dict[str, Any]]
    provider_status: List[Dict[str, Any]]


# Search Schemas
class HealthPlanProviderSearch(BaseModel):
    name: Optional[str] = None
    status: Optional[IntegrationStatus] = None
    auth_method: Optional[AuthMethod] = None
    supports_authorization: Optional[bool] = None
    supports_eligibility: Optional[bool] = None
    supports_sadt: Optional[bool] = None


class HealthPlanAuthorizationSearch(BaseModel):
    provider_id: Optional[int] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    urgency_level: Optional[str] = None


class HealthPlanEligibilitySearch(BaseModel):
    provider_id: Optional[int] = None
    patient_id: Optional[int] = None
    is_eligible: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
