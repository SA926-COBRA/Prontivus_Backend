from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class VoiceSessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Voice Session schemas
class VoiceSessionBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    clinical_context: Optional[str] = None
    medical_specialty: Optional[str] = None
    session_type: str = Field("consultation", regex="^(consultation|follow_up|procedure|emergency|other)$")
    transcription_language: str = Field("pt-BR", max_length=10)

class VoiceSessionCreate(VoiceSessionBase):
    pass

class VoiceSessionUpdate(BaseModel):
    status: Optional[VoiceSessionStatus] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    audio_file_path: Optional[str] = None
    audio_file_size: Optional[int] = Field(None, ge=0)
    audio_format: Optional[str] = Field(None, max_length=20)
    sample_rate: Optional[int] = Field(None, ge=8000, le=48000)
    channels: Optional[int] = Field(None, ge=1, le=2)
    transcription_status: Optional[TranscriptionStatus] = None
    transcription_text: Optional[str] = None
    transcription_confidence: Optional[float] = Field(None, ge=0, le=1)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_errors: Optional[Dict[str, Any]] = None
    audio_quality_score: Optional[float] = Field(None, ge=0, le=1)
    background_noise_level: Optional[float] = Field(None, ge=0, le=1)
    speech_clarity_score: Optional[float] = Field(None, ge=0, le=1)

class VoiceSession(VoiceSessionBase):
    id: int
    session_id: str
    status: VoiceSessionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int
    audio_file_path: Optional[str] = None
    audio_file_size: Optional[int] = None
    audio_format: str
    sample_rate: int
    channels: int
    transcription_status: TranscriptionStatus
    transcription_text: Optional[str] = None
    transcription_confidence: Optional[float] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_errors: Optional[Dict[str, Any]] = None
    audio_quality_score: Optional[float] = None
    background_noise_level: Optional[float] = None
    speech_clarity_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Voice Transcription schemas
class VoiceTranscriptionBase(BaseModel):
    session_id: int
    segment_number: int = Field(..., ge=1)
    start_time_seconds: float = Field(..., ge=0)
    end_time_seconds: float = Field(..., ge=0)
    duration_seconds: float = Field(..., ge=0)
    original_text: str
    transcription_engine: str = Field(..., max_length=50)
    language_detected: Optional[str] = Field(None, max_length=10)
    processing_time_seconds: Optional[float] = Field(None, ge=0)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    medical_terms_detected: Optional[List[str]] = None
    drug_names_detected: Optional[List[str]] = None
    anatomical_terms_detected: Optional[List[str]] = None
    audio_quality_segment: Optional[float] = Field(None, ge=0, le=1)
    speech_clarity_segment: Optional[float] = Field(None, ge=0, le=1)

    @validator('end_time_seconds')
    def validate_end_time(cls, v, values):
        if 'start_time_seconds' in values and v <= values['start_time_seconds']:
            raise ValueError('end_time_seconds must be greater than start_time_seconds')
        return v

class VoiceTranscriptionCreate(VoiceTranscriptionBase):
    pass

class VoiceTranscriptionUpdate(BaseModel):
    corrected_text: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    medical_terms_detected: Optional[List[str]] = None
    drug_names_detected: Optional[List[str]] = None
    anatomical_terms_detected: Optional[List[str]] = None
    audio_quality_segment: Optional[float] = Field(None, ge=0, le=1)
    speech_clarity_segment: Optional[float] = Field(None, ge=0, le=1)

class VoiceTranscription(VoiceTranscriptionBase):
    id: int
    corrected_text: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Clinical Voice Note schemas
class ClinicalVoiceNoteBase(BaseModel):
    session_id: int
    note_type: str = Field(..., regex="^(progress_note|assessment|plan|procedure|emergency|other)$")
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment_and_plan: Optional[str] = None
    medications: Optional[List[str]] = None
    diagnoses: Optional[List[str]] = None

class ClinicalVoiceNoteCreate(ClinicalVoiceNoteBase):
    pass

class ClinicalVoiceNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment_and_plan: Optional[str] = None
    medications: Optional[List[str]] = None
    diagnoses: Optional[List[str]] = None
    ai_processed: Optional[bool] = None
    ai_confidence_score: Optional[float] = Field(None, ge=0, le=1)
    ai_suggestions: Optional[Dict[str, Any]] = None
    medical_entities_extracted: Optional[Dict[str, Any]] = None
    reviewed_by_doctor: Optional[bool] = None
    reviewed_at: Optional[datetime] = None
    approved_by_doctor: Optional[bool] = None
    approved_at: Optional[datetime] = None
    doctor_notes: Optional[str] = None
    integrated_to_medical_record: Optional[bool] = None
    medical_record_id: Optional[int] = None

class ClinicalVoiceNote(ClinicalVoiceNoteBase):
    id: int
    ai_processed: bool
    ai_confidence_score: Optional[float] = None
    ai_suggestions: Optional[Dict[str, Any]] = None
    medical_entities_extracted: Optional[Dict[str, Any]] = None
    reviewed_by_doctor: bool
    reviewed_at: Optional[datetime] = None
    approved_by_doctor: bool
    approved_at: Optional[datetime] = None
    doctor_notes: Optional[str] = None
    integrated_to_medical_record: bool
    medical_record_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Voice Processing Job schemas
class VoiceProcessingJobBase(BaseModel):
    session_id: int
    job_type: str = Field(..., regex="^(transcription|analysis|note_generation|quality_check)$")
    parameters: Optional[Dict[str, Any]] = None

class VoiceProcessingJobCreate(VoiceProcessingJobBase):
    pass

class VoiceProcessingJobUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(pending|running|completed|failed)$")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_engine: Optional[str] = Field(None, max_length=50)
    processing_time_seconds: Optional[float] = Field(None, ge=0)
    resource_usage: Optional[Dict[str, Any]] = None

class VoiceProcessingJob(VoiceProcessingJobBase):
    id: int
    job_id: str
    status: str
    progress_percentage: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_engine: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    resource_usage: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Voice Configuration schemas
class VoiceConfigurationBase(BaseModel):
    config_name: str = Field(..., min_length=1, max_length=100)
    config_type: str = Field(..., regex="^(transcription|analysis|quality|general)$")
    settings: Dict[str, Any]
    is_active: bool = True
    is_default: bool = False

class VoiceConfigurationCreate(VoiceConfigurationBase):
    pass

class VoiceConfigurationUpdate(BaseModel):
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)
    config_type: Optional[str] = Field(None, regex="^(transcription|analysis|quality|general)$")
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class VoiceConfiguration(VoiceConfigurationBase):
    id: int
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Voice Analytics schemas
class VoiceAnalyticsBase(BaseModel):
    date: datetime
    period_type: str = Field(..., regex="^(daily|weekly|monthly)$")
    total_sessions: int = Field(0, ge=0)
    total_duration_minutes: float = Field(0, ge=0)
    total_transcriptions: int = Field(0, ge=0)
    total_notes_generated: int = Field(0, ge=0)
    average_audio_quality: Optional[float] = Field(None, ge=0, le=1)
    average_transcription_confidence: Optional[float] = Field(None, ge=0, le=1)
    average_processing_time_seconds: Optional[float] = Field(None, ge=0)
    failed_transcriptions: int = Field(0, ge=0)
    failed_sessions: int = Field(0, ge=0)
    error_rate: float = Field(0, ge=0, le=1)
    active_doctors: int = Field(0, ge=0)
    active_patients: int = Field(0, ge=0)
    peak_usage_hour: Optional[int] = Field(None, ge=0, le=23)
    average_session_duration_minutes: Optional[float] = Field(None, ge=0)

class VoiceAnalyticsCreate(VoiceAnalyticsBase):
    pass

class VoiceAnalytics(VoiceAnalyticsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Request/Response schemas
class VoiceSessionStartRequest(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    clinical_context: Optional[str] = None
    medical_specialty: Optional[str] = None
    session_type: str = Field("consultation", regex="^(consultation|follow_up|procedure|emergency|other)$")
    transcription_language: str = Field("pt-BR", max_length=10)

class VoiceSessionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

class VoiceAudioUploadRequest(BaseModel):
    session_id: str
    audio_data: str  # Base64 encoded audio data
    audio_format: str = Field("wav", regex="^(wav|mp3|m4a|flac)$")
    sample_rate: Optional[int] = Field(16000, ge=8000, le=48000)
    channels: Optional[int] = Field(1, ge=1, le=2)

class VoiceAudioUploadResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None

class VoiceTranscriptionRequest(BaseModel):
    session_id: str
    transcription_engine: str = Field("whisper", regex="^(whisper|google|azure|aws)$")
    language: Optional[str] = Field("pt-BR", max_length=10)
    enable_medical_terminology: bool = True
    enable_drug_detection: bool = True
    enable_anatomical_detection: bool = True

class VoiceTranscriptionResponse(BaseModel):
    success: bool
    message: str
    transcription_id: Optional[str] = None
    estimated_processing_time: Optional[int] = None

class VoiceNoteGenerationRequest(BaseModel):
    session_id: str
    note_type: str = Field("progress_note", regex="^(progress_note|assessment|plan|procedure|emergency|other)$")
    include_ai_analysis: bool = True
    auto_extract_entities: bool = True
    generate_suggestions: bool = True

class VoiceNoteGenerationResponse(BaseModel):
    success: bool
    message: str
    note_id: Optional[int] = None
    estimated_processing_time: Optional[int] = None

class VoiceSessionEndRequest(BaseModel):
    session_id: str
    auto_transcribe: bool = True
    auto_generate_note: bool = False

class VoiceSessionEndResponse(BaseModel):
    success: bool
    message: str
    session_duration: Optional[int] = None
    transcription_job_id: Optional[str] = None
    note_generation_job_id: Optional[str] = None

# Dashboard and Analytics schemas
class VoiceDashboardStats(BaseModel):
    active_sessions: int
    total_sessions_today: int
    total_duration_today_minutes: float
    average_session_duration_minutes: float
    transcription_success_rate: float
    average_audio_quality: float
    pending_transcriptions: int
    completed_notes_today: int
    most_active_doctors: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]

class VoiceAnalyticsSummary(BaseModel):
    total_sessions: int
    total_duration_hours: float
    total_transcriptions: int
    total_notes_generated: int
    average_audio_quality: float
    average_transcription_confidence: float
    error_rate: float
    most_used_specialties: List[Dict[str, Any]]
    usage_trends: List[Dict[str, Any]]
    quality_metrics: Dict[str, Any]

# Quality Assessment schemas
class VoiceQualityAssessment(BaseModel):
    audio_quality_score: float = Field(..., ge=0, le=1)
    background_noise_level: float = Field(..., ge=0, le=1)
    speech_clarity_score: float = Field(..., ge=0, le=1)
    overall_quality: str = Field(..., regex="^(excellent|good|fair|poor)$")
    recommendations: List[str] = []

class VoiceProcessingStatus(BaseModel):
    session_id: str
    status: str
    progress_percentage: int
    current_step: str
    estimated_completion_time: Optional[int] = None
    error_message: Optional[str] = None
