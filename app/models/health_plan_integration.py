"""
Health Plan Integration Models
Centralized panel for managing all provider APIs (authorizations, eligibility, SADT)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid
from datetime import datetime
import enum


class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"


class AuthMethod(str, enum.Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"


class HealthPlanProvider(Base):
    """Health plan providers (Unimed, Bradesco Saúde, etc.)"""
    __tablename__ = "health_plan_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    code = Column(String(50), unique=True, index=True)
    cnpj = Column(String(18), unique=True)
    website = Column(String(500))
    description = Column(Text)
    
    # API Configuration
    base_url = Column(String(500), nullable=False)
    auth_method = Column(Enum(AuthMethod), default=AuthMethod.OAUTH2)
    api_version = Column(String(20), default="v1")
    
    # OAuth Configuration
    client_id = Column(String(200))
    client_secret = Column(String(500))  # Encrypted
    scope = Column(String(500))
    audience = Column(String(500))
    authorization_url = Column(String(500))
    token_url = Column(String(500))
    
    # API Key Configuration
    api_key = Column(String(500))  # Encrypted
    api_key_header = Column(String(100), default="X-API-Key")
    
    # Basic Auth Configuration
    username = Column(String(200))
    password = Column(String(500))  # Encrypted
    
    # Bearer Token Configuration
    bearer_token = Column(String(500))  # Encrypted
    
    # Additional Configuration
    additional_config = Column(JSON)
    requires_doctor_id = Column(Boolean, default=False)
    supports_authorization = Column(Boolean, default=True)
    supports_eligibility = Column(Boolean, default=True)
    supports_sadt = Column(Boolean, default=True)
    
    # Status and Monitoring
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.INACTIVE)
    last_connection_test = Column(DateTime)
    last_connection_status = Column(String(20))  # success, error, timeout
    last_error_message = Column(Text)
    connection_timeout = Column(Integer, default=30)  # seconds
    
    # Audit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    api_endpoints = relationship("HealthPlanAPIEndpoint", back_populates="provider")
    connection_logs = relationship("HealthPlanConnectionLog", back_populates="provider")


class HealthPlanAPIEndpoint(Base):
    """API endpoints for each health plan provider"""
    __tablename__ = "health_plan_api_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("health_plan_providers.id"), nullable=False)
    
    # Endpoint Configuration
    name = Column(String(200), nullable=False)
    endpoint_type = Column(String(50), nullable=False)  # authorization, eligibility, sadt, etc.
    url = Column(String(500), nullable=False)
    method = Column(String(10), default="POST")  # GET, POST, PUT, DELETE
    
    # Request Configuration
    headers = Column(JSON)  # Additional headers
    request_format = Column(String(50), default="json")  # json, xml, form
    response_format = Column(String(50), default="json")  # json, xml
    
    # Authentication
    requires_auth = Column(Boolean, default=True)
    auth_type = Column(String(50))  # Inherit from provider or override
    
    # Rate Limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = relationship("HealthPlanProvider", back_populates="api_endpoints")


class HealthPlanConnectionLog(Base):
    """Log of API connections and responses"""
    __tablename__ = "health_plan_connection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("health_plan_providers.id"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("health_plan_api_endpoints.id"))
    
    # Request Details
    request_url = Column(String(500), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_headers = Column(JSON)
    request_body = Column(Text)
    
    # Response Details
    response_status_code = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    response_time_ms = Column(Integer)
    
    # Error Details
    error_message = Column(Text)
    error_type = Column(String(100))
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    request_type = Column(String(50))  # authorization, eligibility, sadt
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    provider = relationship("HealthPlanProvider", back_populates="connection_logs")
    endpoint = relationship("HealthPlanAPIEndpoint")
    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("Patient")


class HealthPlanAuthorization(Base):
    """Authorization requests to health plans"""
    __tablename__ = "health_plan_authorizations"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("health_plan_providers.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Authorization Details
    authorization_number = Column(String(100), unique=True, index=True)
    procedure_code = Column(String(50), nullable=False)
    procedure_description = Column(String(500))
    requested_date = Column(DateTime, nullable=False)
    requested_quantity = Column(Integer, default=1)
    
    # Patient Information
    patient_cpf = Column(String(14), nullable=False)
    patient_name = Column(String(200), nullable=False)
    patient_dob = Column(DateTime)
    patient_phone = Column(String(20))
    
    # Doctor Information
    doctor_crm = Column(String(20), nullable=False)
    doctor_name = Column(String(200), nullable=False)
    
    # Clinical Information
    clinical_indication = Column(Text, nullable=False)
    clinical_question = Column(Text)
    urgency_level = Column(String(20), default="routine")  # emergency, urgent, routine
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, denied, expired
    authorization_code = Column(String(100))
    approval_date = Column(DateTime)
    expiration_date = Column(DateTime)
    denial_reason = Column(Text)
    
    # API Response
    api_request_id = Column(String(100))
    api_response = Column(JSON)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = relationship("HealthPlanProvider")
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])


class HealthPlanEligibility(Base):
    """Eligibility verification requests"""
    __tablename__ = "health_plan_eligibility"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("health_plan_providers.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Eligibility Details
    eligibility_number = Column(String(100), unique=True, index=True)
    verification_date = Column(DateTime, nullable=False)
    
    # Patient Information
    patient_cpf = Column(String(14), nullable=False)
    patient_name = Column(String(200), nullable=False)
    patient_dob = Column(DateTime)
    
    # Plan Information
    plan_number = Column(String(100))
    plan_name = Column(String(200))
    plan_type = Column(String(100))
    
    # Eligibility Status
    is_eligible = Column(Boolean)
    eligibility_status = Column(String(50))  # active, inactive, suspended, expired
    coverage_start_date = Column(DateTime)
    coverage_end_date = Column(DateTime)
    
    # Coverage Details
    coverage_details = Column(JSON)
    copay_amount = Column(Float)
    deductible_amount = Column(Float)
    
    # API Response
    api_request_id = Column(String(100))
    api_response = Column(JSON)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = relationship("HealthPlanProvider")
    patient = relationship("Patient")


class HealthPlanConfiguration(Base):
    """Global configuration for health plan integrations"""
    __tablename__ = "health_plan_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Global Settings
    default_timeout = Column(Integer, default=30)
    max_retry_attempts = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)
    
    # Logging Settings
    log_all_requests = Column(Boolean, default=True)
    log_response_bodies = Column(Boolean, default=False)
    log_retention_days = Column(Integer, default=90)
    
    # Security Settings
    encrypt_sensitive_data = Column(Boolean, default=True)
    mask_logs = Column(Boolean, default=True)
    
    # Notification Settings
    notify_on_errors = Column(Boolean, default=True)
    notify_on_slow_requests = Column(Boolean, default=True)
    slow_request_threshold_ms = Column(Integer, default=5000)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
