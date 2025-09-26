from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.database.database import Base

class AIProvider(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"

class AITaskType(enum.Enum):
    PRE_CONSULTATION_SUMMARY = "pre_consultation_summary"
    MEDICAL_TRANSCRIPTION = "medical_transcription"
    CLINICAL_NOTES = "clinical_notes"
    DIAGNOSIS_SUGGESTION = "diagnosis_suggestion"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    DRUG_INTERACTION_CHECK = "drug_interaction_check"
    MEDICAL_QA = "medical_qa"
    DOCUMENT_ANALYSIS = "document_analysis"

class AIProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIConfiguration(Base):
    """AI service configuration and settings"""
    __tablename__ = "ai_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    configuration_name = Column(String(200), nullable=False)
    provider = Column(Enum(AIProvider), nullable=False)
    
    # Provider Configuration
    api_endpoint = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    
    # Processing Settings
    max_tokens = Column(Integer, default=4000)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    
    # Task-specific Settings
    task_type = Column(Enum(AITaskType), nullable=False)
    prompt_template = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    
    # Performance Settings
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    batch_size = Column(Integer, default=1)
    
    # Status and Monitoring
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    average_response_time = Column(Float, nullable=True)
    
    # Cost Tracking
    cost_per_token = Column(Numeric(10, 6), nullable=True)
    total_cost = Column(Numeric(10, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    processing_jobs = relationship("AIProcessingJob", back_populates="configuration")

class AIProcessingJob(Base):
    """AI processing job tracking and results"""
    __tablename__ = "ai_processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False)
    
    # Job Information
    configuration_id = Column(Integer, ForeignKey("ai_configurations.id"), nullable=False)
    task_type = Column(Enum(AITaskType), nullable=False)
    
    # Input Data
    input_data = Column(JSON, nullable=False)
    input_text = Column(Text, nullable=True)
    input_metadata = Column(JSON, nullable=True)
    
    # Processing Details
    status = Column(Enum(AIProcessingStatus), default=AIProcessingStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Results
    output_data = Column(JSON, nullable=True)
    output_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Usage Tracking
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Numeric(10, 4), nullable=True)
    
    # Related Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    configuration = relationship("AIConfiguration", back_populates="processing_jobs")
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    creator = relationship("User", foreign_keys=[created_by])

class PreConsultationSummary(Base):
    """Pre-consultation AI-generated summaries"""
    __tablename__ = "pre_consultation_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(String(100), unique=True, nullable=False)
    
    # Related Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    processing_job_id = Column(Integer, ForeignKey("ai_processing_jobs.id"), nullable=True)
    
    # Summary Content
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    social_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    review_of_systems = Column(Text, nullable=True)
    
    # AI Analysis
    risk_factors = Column(JSON, nullable=True)
    potential_diagnoses = Column(JSON, nullable=True)
    recommended_tests = Column(JSON, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status and Review
    status = Column(String(50), default="generated")  # generated, reviewed, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    processing_job = relationship("AIProcessingJob")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])

class MedicalTranscription(Base):
    """AI-generated medical transcriptions"""
    __tablename__ = "medical_transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(String(100), unique=True, nullable=False)
    
    # Related Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    processing_job_id = Column(Integer, ForeignKey("ai_processing_jobs.id"), nullable=True)
    
    # Audio Information
    audio_file_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    audio_quality = Column(String(50), nullable=True)
    
    # Transcription Content
    raw_transcription = Column(Text, nullable=True)
    cleaned_transcription = Column(Text, nullable=True)
    structured_transcription = Column(JSON, nullable=True)
    
    # AI Analysis
    speaker_identification = Column(JSON, nullable=True)
    medical_terms = Column(JSON, nullable=True)
    key_phrases = Column(JSON, nullable=True)
    sentiment_analysis = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status and Review
    status = Column(String(50), default="transcribed")  # transcribed, reviewed, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    processing_job = relationship("AIProcessingJob")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])

class ClinicalNotes(Base):
    """AI-generated clinical notes"""
    __tablename__ = "clinical_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    notes_id = Column(String(100), unique=True, nullable=False)
    
    # Related Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    processing_job_id = Column(Integer, ForeignKey("ai_processing_jobs.id"), nullable=True)
    
    # Notes Content
    subjective = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    
    # AI Analysis
    diagnosis_suggestions = Column(JSON, nullable=True)
    treatment_recommendations = Column(JSON, nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    risk_assessment = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status and Review
    status = Column(String(50), default="generated")  # generated, reviewed, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    processing_job = relationship("AIProcessingJob")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])

class AIUsageLog(Base):
    """AI usage tracking and analytics"""
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Usage Information
    configuration_id = Column(Integer, ForeignKey("ai_configurations.id"), nullable=False)
    processing_job_id = Column(Integer, ForeignKey("ai_processing_jobs.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Request Details
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    task_type = Column(Enum(AITaskType), nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Response Details
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Cost Information
    cost = Column(Numeric(10, 4), nullable=True)
    cost_per_token = Column(Numeric(10, 6), nullable=True)
    
    # Additional Data
    usage_metadata = Column(JSON, nullable=True)
    
    # Relationships
    configuration = relationship("AIConfiguration")
    processing_job = relationship("AIProcessingJob")
    user = relationship("User")

class AIModel(Base):
    """AI model information and performance tracking"""
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    provider = Column(Enum(AIProvider), nullable=False)
    
    # Model Information
    model_type = Column(String(50), nullable=False)  # gpt, claude, gemini, etc.
    model_size = Column(String(50), nullable=True)  # small, medium, large, xl
    capabilities = Column(JSON, nullable=True)  # List of supported tasks
    
    # Performance Metrics
    accuracy_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    cost_per_token = Column(Numeric(10, 6), nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Usage Statistics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    average_response_time = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    configurations = relationship("AIConfiguration")

class AIFeedback(Base):
    """User feedback on AI-generated content"""
    __tablename__ = "ai_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Related Information
    processing_job_id = Column(Integer, ForeignKey("ai_processing_jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Feedback Details
    feedback_type = Column(String(50), nullable=False)  # accuracy, relevance, completeness, etc.
    rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)
    
    # Content Analysis
    content_quality = Column(String(50), nullable=True)  # excellent, good, fair, poor
    accuracy_rating = Column(Integer, nullable=True)  # 1-5 scale
    relevance_rating = Column(Integer, nullable=True)  # 1-5 scale
    completeness_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    processing_job = relationship("AIProcessingJob")
    user = relationship("User")
