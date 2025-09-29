from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.models.base import Base

class IntegrationType(enum.Enum):
    HEALTH_PLAN = "health_plan"
    TELEMEDICINE = "telemedicine"
    EMR = "emr"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PHARMACY = "pharmacy"
    PAYMENT = "payment"

class IntegrationStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class HealthPlanType(enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"

class TelemedicineProvider(enum.Enum):
    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    WEBEX = "webex"
    CUSTOM = "custom"

class HealthPlanIntegration(Base):
    """Health plan integration configuration and management"""
    __tablename__ = "health_plan_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_name = Column(String(200), nullable=False)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=False)
    
    # Integration Configuration
    integration_type = Column(Enum(IntegrationType), default=IntegrationType.HEALTH_PLAN)
    api_endpoint = Column(String(500), nullable=False)
    api_version = Column(String(20), nullable=True)
    authentication_method = Column(String(50), nullable=False)  # oauth, api_key, basic_auth
    
    # Authentication Details
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True)  # Additional configuration
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(200), nullable=True)
    
    # Status and Monitoring
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.PENDING)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Health Plan Specific
    plan_code = Column(String(100), nullable=True)
    plan_name = Column(String(200), nullable=True)
    coverage_details = Column(JSON, nullable=True)
    copayment_info = Column(JSON, nullable=True)
    authorization_required = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_plan = relationship("HealthPlan")
    creator = relationship("User", foreign_keys=[created_by])
    sync_logs = relationship("IntegrationSyncLog", back_populates="integration")

class TelemedicineIntegration(Base):
    """Telemedicine platform integration"""
    __tablename__ = "telemedicine_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_name = Column(String(200), nullable=False)
    provider = Column(Enum(TelemedicineProvider), nullable=False)
    
    # Provider Configuration
    api_endpoint = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=True)
    api_secret = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(200), nullable=True)
    
    # Authentication
    authentication_method = Column(String(50), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True)
    default_settings = Column(JSON, nullable=True)  # Default meeting settings
    
    # Status and Monitoring
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.PENDING)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Telemedicine Specific
    max_participants = Column(Integer, default=100)
    recording_enabled = Column(Boolean, default=True)
    waiting_room_enabled = Column(Boolean, default=True)
    breakout_rooms_enabled = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    sync_logs = relationship("IntegrationSyncLog", back_populates="telemedicine_integration")

class IntegrationSyncLog(Base):
    """Integration synchronization logs"""
    __tablename__ = "integration_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Integration References
    integration_id = Column(Integer, ForeignKey("health_plan_integrations.id"), nullable=True)
    telemedicine_integration_id = Column(Integer, ForeignKey("telemedicine_integrations.id"), nullable=True)
    
    # Sync Details
    sync_type = Column(String(50), nullable=False)  # data_sync, auth_sync, webhook, etc.
    sync_start = Column(DateTime(timezone=True), nullable=False)
    sync_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed
    
    # Sync Data
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Additional Data
    sync_data = Column(JSON, nullable=True)
    sync_metadata = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    integration = relationship("HealthPlanIntegration", back_populates="sync_logs")
    telemedicine_integration = relationship("TelemedicineIntegration", back_populates="sync_logs")

# HealthPlanAuthorization model is now defined in health_plan_integration.py
# Removed to avoid duplicate table definition

class IntegrationWebhook(Base):
    """Webhook configurations for integrations"""
    __tablename__ = "integration_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_name = Column(String(200), nullable=False)
    
    # Integration References
    integration_id = Column(Integer, ForeignKey("health_plan_integrations.id"), nullable=True)
    telemedicine_integration_id = Column(Integer, ForeignKey("telemedicine_integrations.id"), nullable=True)
    
    # Webhook Configuration
    webhook_url = Column(String(500), nullable=False)
    webhook_secret = Column(String(200), nullable=True)
    events = Column(JSON, nullable=False)  # List of events to listen for
    
    # Authentication
    authentication_method = Column(String(50), default="none")  # none, basic_auth, bearer_token, signature
    auth_username = Column(String(100), nullable=True)
    auth_password = Column(String(200), nullable=True)
    auth_token = Column(String(500), nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    
    # Status and Monitoring
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    integration = relationship("HealthPlanIntegration")
    telemedicine_integration = relationship("TelemedicineIntegration")
    creator = relationship("User", foreign_keys=[created_by])
    logs = relationship("WebhookLog", back_populates="webhook")

class WebhookLog(Base):
    """Webhook execution logs"""
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("integration_webhooks.id"), nullable=False)
    
    # Request Details
    request_url = Column(String(500), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(Text, nullable=True)
    
    # Response Details
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Execution Details
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Additional Data
    event_type = Column(String(100), nullable=True)
    event_data = Column(JSON, nullable=True)
    
    # Relationships
    webhook = relationship("IntegrationWebhook", back_populates="logs")

class IntegrationHealthCheck(Base):
    """Integration health check results"""
    __tablename__ = "integration_health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Integration References
    integration_id = Column(Integer, ForeignKey("health_plan_integrations.id"), nullable=True)
    telemedicine_integration_id = Column(Integer, ForeignKey("telemedicine_integrations.id"), nullable=True)
    
    # Health Check Details
    check_type = Column(String(50), nullable=False)  # connectivity, authentication, api, etc.
    check_start = Column(DateTime(timezone=True), nullable=False)
    check_end = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    status = Column(String(20), nullable=False)  # healthy, unhealthy, warning
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metrics
    metrics = Column(JSON, nullable=True)  # Additional metrics
    details = Column(JSON, nullable=True)  # Detailed results
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    integration = relationship("HealthPlanIntegration")
    telemedicine_integration = relationship("TelemedicineIntegration")
