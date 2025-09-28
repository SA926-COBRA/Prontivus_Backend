"""
AI Integration Models
Models for AI-powered medical consultation analysis
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum


class AIProvider(str, enum.Enum):
    """AI service providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"


class AIAnalysisStatus(str, enum.Enum):
    """AI analysis status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIAnalysisType(str, enum.Enum):
    """Types of AI analysis"""
    TRANSCRIPTION = "transcription"
    CLINICAL_SUMMARY = "clinical_summary"
    DIAGNOSIS_SUGGESTION = "diagnosis_suggestion"
    EXAM_SUGGESTION = "exam_suggestion"
    TREATMENT_SUGGESTION = "treatment_suggestion"
    ICD_CODING = "icd_coding"
    PRESCRIPTION_SUGGESTION = "prescription_suggestion"


class AIAnalysisSession(Base):
    """AI analysis session for medical consultations"""
    __tablename__ = "ai_analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Session details
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    consultation_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    telemedicine_session_id = Column(Integer, ForeignKey("telemedicine_sessions.id"), nullable=True, index=True)
    
    # Participants
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Audio/Video data
    audio_file_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Integer, nullable=True)
    audio_file_size_mb = Column(Float, nullable=True)
    video_file_path = Column(String(500), nullable=True)
    
    # AI Configuration
    ai_provider = Column(Enum(AIProvider), nullable=False)
    ai_model = Column(String(100), nullable=False)
    language = Column(String(10), default="pt-BR")
    
    # Analysis settings
    enabled_analyses = Column(JSON, nullable=True)  # List of enabled analysis types
    custom_prompts = Column(JSON, nullable=True)  # Custom prompts for each analysis type
    
    # Status and results
    status = Column(Enum(AIAnalysisStatus), default=AIAnalysisStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Cost tracking
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    
    # Consent and privacy
    patient_consent_given = Column(Boolean, default=False)
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    data_retention_days = Column(Integer, default=30)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    consultation = relationship("Appointment")
    telemedicine_session = relationship("TelemedicineSession")
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient")
    analyses = relationship("AIAnalysis", back_populates="session")


class AIAnalysis(Base):
    """Individual AI analysis results"""
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_analysis_sessions.id"), nullable=False, index=True)
    
    # Analysis details
    analysis_type = Column(Enum(AIAnalysisType), nullable=False)
    analysis_version = Column(String(20), default="1.0")
    
    # Input data
    input_text = Column(Text, nullable=True)  # Transcribed text or input prompt
    input_audio_segment_start = Column(Integer, nullable=True)  # Start time in seconds
    input_audio_segment_end = Column(Integer, nullable=True)  # End time in seconds
    
    # AI processing
    ai_provider = Column(Enum(AIProvider), nullable=False)
    ai_model = Column(String(100), nullable=False)
    prompt_used = Column(Text, nullable=True)
    
    # Results
    raw_result = Column(Text, nullable=True)  # Raw AI response
    processed_result = Column(JSON, nullable=True)  # Structured result
    confidence_score = Column(Float, nullable=True)  # AI confidence (0-1)
    
    # Status
    status = Column(Enum(AIAnalysisStatus), default=AIAnalysisStatus.PENDING)
    processing_time_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Cost tracking
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    
    # Doctor review
    doctor_reviewed = Column(Boolean, default=False)
    doctor_approved = Column(Boolean, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    doctor_modified_result = Column(JSON, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session = relationship("AIAnalysisSession", back_populates="analyses")


class AIConfiguration(Base):
    """AI service configuration for tenants"""
    __tablename__ = "ai_configuration"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Service settings
    is_enabled = Column(Boolean, default=False)
    default_provider = Column(Enum(AIProvider), default=AIProvider.OPENAI)
    default_model = Column(String(100), default="gpt-4")
    default_language = Column(String(10), default="pt-BR")
    
    # API credentials (encrypted)
    openai_api_key = Column(String(500), nullable=True)  # Encrypted
    anthropic_api_key = Column(String(500), nullable=True)  # Encrypted
    google_api_key = Column(String(500), nullable=True)  # Encrypted
    azure_endpoint = Column(String(500), nullable=True)
    azure_api_key = Column(String(500), nullable=True)  # Encrypted
    
    # Analysis settings
    enabled_analyses = Column(JSON, nullable=True)  # Default enabled analyses
    transcription_enabled = Column(Boolean, default=True)
    clinical_summary_enabled = Column(Boolean, default=True)
    diagnosis_suggestion_enabled = Column(Boolean, default=True)
    exam_suggestion_enabled = Column(Boolean, default=True)
    treatment_suggestion_enabled = Column(Boolean, default=True)
    icd_coding_enabled = Column(Boolean, default=True)
    prescription_suggestion_enabled = Column(Boolean, default=True)
    
    # Quality settings
    min_confidence_threshold = Column(Float, default=0.7)
    max_analysis_duration_minutes = Column(Integer, default=60)
    auto_approve_low_risk = Column(Boolean, default=False)
    
    # Cost management
    monthly_budget_usd = Column(Float, nullable=True)
    cost_per_analysis_usd = Column(Float, nullable=True)
    alert_threshold_percent = Column(Integer, default=80)  # Alert when 80% of budget used
    
    # Privacy and compliance
    data_retention_days = Column(Integer, default=30)
    auto_delete_enabled = Column(Boolean, default=True)
    anonymize_data = Column(Boolean, default=True)
    lgpd_compliant = Column(Boolean, default=True)
    
    # Integration settings
    integrate_with_emr = Column(Boolean, default=True)
    auto_populate_notes = Column(Boolean, default=False)
    require_doctor_approval = Column(Boolean, default=True)
    
    # Custom prompts
    custom_prompts = Column(JSON, nullable=True)  # Custom prompts for each analysis type
    
    # Notification settings
    notify_on_completion = Column(Boolean, default=True)
    notify_on_error = Column(Boolean, default=True)
    notify_on_budget_alert = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")


class AIUsageAnalytics(Base):
    """Analytics for AI usage and costs"""
    __tablename__ = "ai_usage_analytics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # Usage metrics
    total_sessions = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)
    total_audio_minutes = Column(Float, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    # Cost metrics
    total_cost_usd = Column(Float, default=0)
    average_cost_per_session = Column(Float, default=0)
    average_cost_per_analysis = Column(Float, default=0)
    
    # Quality metrics
    average_confidence_score = Column(Float, default=0)
    doctor_approval_rate = Column(Float, default=0)
    auto_approval_rate = Column(Float, default=0)
    
    # Analysis breakdown
    transcription_count = Column(Integer, default=0)
    clinical_summary_count = Column(Integer, default=0)
    diagnosis_suggestion_count = Column(Integer, default=0)
    exam_suggestion_count = Column(Integer, default=0)
    treatment_suggestion_count = Column(Integer, default=0)
    icd_coding_count = Column(Integer, default=0)
    prescription_suggestion_count = Column(Integer, default=0)
    
    # Provider breakdown
    openai_usage_count = Column(Integer, default=0)
    anthropic_usage_count = Column(Integer, default=0)
    google_usage_count = Column(Integer, default=0)
    azure_usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")


class AIPromptTemplate(Base):
    """Template prompts for AI analysis"""
    __tablename__ = "ai_prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(255), nullable=False)
    analysis_type = Column(Enum(AIAnalysisType), nullable=False)
    language = Column(String(10), default="pt-BR")
    version = Column(String(20), default="1.0")
    
    # Template content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    output_format = Column(JSON, nullable=True)  # Expected output format
    
    # Template settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0)
    average_confidence = Column(Float, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")