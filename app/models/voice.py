from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.database import Base

class VoiceSessionStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class TranscriptionStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VoiceSession(Base):
    """Voice recording sessions for clinical progress notes"""
    __tablename__ = "voice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Session details
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Session metadata
    status = Column(Enum(VoiceSessionStatus), default=VoiceSessionStatus.ACTIVE)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # Audio file information
    audio_file_path = Column(String(500), nullable=True)
    audio_file_size = Column(Integer, nullable=True)
    audio_format = Column(String(20), default="wav")
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    
    # Transcription information
    transcription_status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    transcription_text = Column(Text, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    transcription_language = Column(String(10), default="pt-BR")
    
    # Clinical context
    clinical_context = Column(Text, nullable=True)  # Pre-filled context
    medical_specialty = Column(String(100), nullable=True)
    session_type = Column(String(50), default="consultation")  # consultation, follow_up, procedure, etc.
    
    # Processing information
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_errors = Column(JSON, nullable=True)
    
    # Quality metrics
    audio_quality_score = Column(Float, nullable=True)  # 0-1 score
    background_noise_level = Column(Float, nullable=True)
    speech_clarity_score = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    appointment = relationship("Appointment")
    creator = relationship("User", foreign_keys=[created_by])
    transcriptions = relationship("VoiceTranscription", back_populates="session")
    clinical_notes = relationship("ClinicalVoiceNote", back_populates="session")

class VoiceTranscription(Base):
    """Individual transcription segments from voice sessions"""
    __tablename__ = "voice_transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False)
    
    # Transcription details
    segment_number = Column(Integer, nullable=False)
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Text content
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Processing information
    transcription_engine = Column(String(50), nullable=False)  # whisper, google, azure, etc.
    language_detected = Column(String(10), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Medical terminology
    medical_terms_detected = Column(JSON, nullable=True)  # List of detected medical terms
    drug_names_detected = Column(JSON, nullable=True)  # List of detected drug names
    anatomical_terms_detected = Column(JSON, nullable=True)  # List of anatomical terms
    
    # Quality metrics
    audio_quality_segment = Column(Float, nullable=True)
    speech_clarity_segment = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    session = relationship("VoiceSession", back_populates="transcriptions")

class ClinicalVoiceNote(Base):
    """Clinical notes generated from voice sessions"""
    __tablename__ = "clinical_voice_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False)
    
    # Note details
    note_type = Column(String(50), nullable=False)  # progress_note, assessment, plan, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Clinical information
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    physical_examination = Column(Text, nullable=True)
    assessment_and_plan = Column(Text, nullable=True)
    medications = Column(JSON, nullable=True)  # List of medications mentioned
    diagnoses = Column(JSON, nullable=True)  # List of diagnoses mentioned
    
    # AI processing
    ai_processed = Column(Boolean, default=False)
    ai_confidence_score = Column(Float, nullable=True)
    ai_suggestions = Column(JSON, nullable=True)
    medical_entities_extracted = Column(JSON, nullable=True)
    
    # Review and approval
    reviewed_by_doctor = Column(Boolean, default=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_doctor = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    
    # Integration
    integrated_to_medical_record = Column(Boolean, default=False)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    session = relationship("VoiceSession", back_populates="clinical_notes")
    medical_record = relationship("MedicalRecord")
    creator = relationship("User", foreign_keys=[created_by])

class VoiceProcessingJob(Base):
    """Background jobs for voice processing"""
    __tablename__ = "voice_processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Job details
    session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # transcription, analysis, note_generation
    
    # Job status
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress_percentage = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Job parameters
    parameters = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing information
    processing_engine = Column(String(50), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    resource_usage = Column(JSON, nullable=True)  # CPU, memory usage
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    session = relationship("VoiceSession")

class VoiceConfiguration(Base):
    """Configuration settings for voice processing"""
    __tablename__ = "voice_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration details
    config_name = Column(String(100), nullable=False)
    config_type = Column(String(50), nullable=False)  # transcription, analysis, quality
    
    # Settings
    settings = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class VoiceAnalytics(Base):
    """Analytics and metrics for voice processing"""
    __tablename__ = "voice_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Analytics period
    date = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Usage metrics
    total_sessions = Column(Integer, default=0)
    total_duration_minutes = Column(Float, default=0)
    total_transcriptions = Column(Integer, default=0)
    total_notes_generated = Column(Integer, default=0)
    
    # Quality metrics
    average_audio_quality = Column(Float, nullable=True)
    average_transcription_confidence = Column(Float, nullable=True)
    average_processing_time_seconds = Column(Float, nullable=True)
    
    # Error metrics
    failed_transcriptions = Column(Integer, default=0)
    failed_sessions = Column(Integer, default=0)
    error_rate = Column(Float, default=0)
    
    # User metrics
    active_doctors = Column(Integer, default=0)
    active_patients = Column(Integer, default=0)
    
    # Performance metrics
    peak_usage_hour = Column(Integer, nullable=True)
    average_session_duration_minutes = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
