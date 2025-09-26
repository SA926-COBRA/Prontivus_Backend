from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"

class AITaskType(str, Enum):
    PRE_CONSULTATION_SUMMARY = "pre_consultation_summary"
    MEDICAL_TRANSCRIPTION = "medical_transcription"
    CLINICAL_NOTES = "clinical_notes"
    DIAGNOSIS_SUGGESTION = "diagnosis_suggestion"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    DRUG_INTERACTION_CHECK = "drug_interaction_check"
    MEDICAL_QA = "medical_qa"
    DOCUMENT_ANALYSIS = "document_analysis"

class AIProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# AI Configuration schemas
class AIConfigurationBase(BaseModel):
    configuration_name: str = Field(..., min_length=1, max_length=200)
    provider: AIProvider
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    max_tokens: int = Field(4000, ge=1, le=100000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    task_type: AITaskType
    prompt_template: str
    system_prompt: Optional[str] = None
    timeout_seconds: int = Field(30, ge=5, le=300)
    retry_count: int = Field(3, ge=0, le=10)
    batch_size: int = Field(1, ge=1, le=100)
    cost_per_token: Optional[Decimal] = Field(None, ge=0)

class AIConfigurationCreate(AIConfigurationBase):
    pass

class AIConfigurationUpdate(BaseModel):
    configuration_name: Optional[str] = Field(None, min_length=1, max_length=200)
    provider: Optional[AIProvider] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    task_type: Optional[AITaskType] = None
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    batch_size: Optional[int] = Field(None, ge=1, le=100)
    cost_per_token: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None

class AIConfiguration(AIConfigurationBase):
    id: int
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    success_count: int
    failure_count: int
    average_response_time: Optional[float] = None
    total_cost: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# AI Processing Job schemas
class AIProcessingJobBase(BaseModel):
    configuration_id: int
    task_type: AITaskType
    input_data: Dict[str, Any]
    input_text: Optional[str] = None
    input_metadata: Optional[Dict[str, Any]] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_id: Optional[int] = None

class AIProcessingJobCreate(AIProcessingJobBase):
    pass

class AIProcessingJobUpdate(BaseModel):
    status: Optional[AIProcessingStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    output_data: Optional[Dict[str, Any]] = None
    output_text: Optional[str] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[Decimal] = None

class AIProcessingJob(AIProcessingJobBase):
    id: int
    job_id: str
    status: AIProcessingStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    output_data: Optional[Dict[str, Any]] = None
    output_text: Optional[str] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Pre-Consultation Summary schemas
class PreConsultationSummaryBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    processing_job_id: Optional[int] = None
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    social_history: Optional[str] = None
    family_history: Optional[str] = None
    review_of_systems: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    potential_diagnoses: Optional[Dict[str, Any]] = None
    recommended_tests: Optional[Dict[str, Any]] = None
    clinical_notes: Optional[str] = None
    confidence_score: Optional[float] = None

class PreConsultationSummaryCreate(PreConsultationSummaryBase):
    pass

class PreConsultationSummaryUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    social_history: Optional[str] = None
    family_history: Optional[str] = None
    review_of_systems: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    potential_diagnoses: Optional[Dict[str, Any]] = None
    recommended_tests: Optional[Dict[str, Any]] = None
    clinical_notes: Optional[str] = None
    confidence_score: Optional[float] = None
    status: Optional[str] = None
    review_notes: Optional[str] = None
    is_approved: Optional[bool] = None

class PreConsultationSummary(PreConsultationSummaryBase):
    id: int
    summary_id: str
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Medical Transcription schemas
class MedicalTranscriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    processing_job_id: Optional[int] = None
    audio_file_path: Optional[str] = Field(None, max_length=500)
    audio_duration_seconds: Optional[float] = None
    audio_quality: Optional[str] = Field(None, max_length=50)
    raw_transcription: Optional[str] = None
    cleaned_transcription: Optional[str] = None
    structured_transcription: Optional[Dict[str, Any]] = None
    speaker_identification: Optional[Dict[str, Any]] = None
    medical_terms: Optional[Dict[str, Any]] = None
    key_phrases: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

class MedicalTranscriptionCreate(MedicalTranscriptionBase):
    pass

class MedicalTranscriptionUpdate(BaseModel):
    audio_file_path: Optional[str] = Field(None, max_length=500)
    audio_duration_seconds: Optional[float] = None
    audio_quality: Optional[str] = Field(None, max_length=50)
    raw_transcription: Optional[str] = None
    cleaned_transcription: Optional[str] = None
    structured_transcription: Optional[Dict[str, Any]] = None
    speaker_identification: Optional[Dict[str, Any]] = None
    medical_terms: Optional[Dict[str, Any]] = None
    key_phrases: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    status: Optional[str] = None
    review_notes: Optional[str] = None
    is_approved: Optional[bool] = None

class MedicalTranscription(MedicalTranscriptionBase):
    id: int
    transcription_id: str
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Clinical Notes schemas
class ClinicalNotesBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    processing_job_id: Optional[int] = None
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    diagnosis_suggestions: Optional[Dict[str, Any]] = None
    treatment_recommendations: Optional[Dict[str, Any]] = None
    follow_up_notes: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

class ClinicalNotesCreate(ClinicalNotesBase):
    pass

class ClinicalNotesUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    diagnosis_suggestions: Optional[Dict[str, Any]] = None
    treatment_recommendations: Optional[Dict[str, Any]] = None
    follow_up_notes: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    status: Optional[str] = None
    review_notes: Optional[str] = None
    is_approved: Optional[bool] = None

class ClinicalNotes(ClinicalNotesBase):
    id: int
    notes_id: str
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# AI Usage Log schemas
class AIUsageLogBase(BaseModel):
    configuration_id: int
    processing_job_id: Optional[int] = None
    user_id: Optional[int] = None
    task_type: AITaskType
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    response_time_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    cost: Optional[Decimal] = None
    cost_per_token: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None

class AIUsageLogCreate(AIUsageLogBase):
    pass

class AIUsageLog(AIUsageLogBase):
    id: int
    request_timestamp: datetime

    class Config:
        from_attributes = True

# AI Model schemas
class AIModelBase(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    provider: AIProvider
    model_type: str = Field(..., min_length=1, max_length=50)
    model_size: Optional[str] = Field(None, max_length=50)
    capabilities: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = None
    response_time_ms: Optional[int] = None
    cost_per_token: Optional[Decimal] = None
    max_tokens: Optional[int] = None

class AIModelCreate(AIModelBase):
    pass

class AIModelUpdate(BaseModel):
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    provider: Optional[AIProvider] = None
    model_type: Optional[str] = Field(None, min_length=1, max_length=50)
    model_size: Optional[str] = Field(None, max_length=50)
    capabilities: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = None
    response_time_ms: Optional[int] = None
    cost_per_token: Optional[Decimal] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    is_deprecated: Optional[bool] = None

class AIModel(AIModelBase):
    id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: Optional[float] = None
    is_active: bool
    is_deprecated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# AI Feedback schemas
class AIFeedbackBase(BaseModel):
    processing_job_id: int
    user_id: int
    feedback_type: str = Field(..., min_length=1, max_length=50)
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    suggestions: Optional[str] = None
    content_quality: Optional[str] = Field(None, max_length=50)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    relevance_rating: Optional[int] = Field(None, ge=1, le=5)
    completeness_rating: Optional[int] = Field(None, ge=1, le=5)

class AIFeedbackCreate(AIFeedbackBase):
    pass

class AIFeedbackUpdate(BaseModel):
    feedback_type: Optional[str] = Field(None, min_length=1, max_length=50)
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    suggestions: Optional[str] = None
    content_quality: Optional[str] = Field(None, max_length=50)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    relevance_rating: Optional[int] = Field(None, ge=1, le=5)
    completeness_rating: Optional[int] = Field(None, ge=1, le=5)

class AIFeedback(AIFeedbackBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Request/Response schemas
class AIProcessingRequest(BaseModel):
    configuration_id: int
    input_data: Dict[str, Any]
    input_text: Optional[str] = None
    input_metadata: Optional[Dict[str, Any]] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_id: Optional[int] = None

class PreConsultationSummaryRequest(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    patient_data: Dict[str, Any]
    medical_history: Optional[Dict[str, Any]] = None
    current_symptoms: Optional[Dict[str, Any]] = None

class MedicalTranscriptionRequest(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    audio_file_path: str
    audio_metadata: Optional[Dict[str, Any]] = None

class ClinicalNotesRequest(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    consultation_data: Dict[str, Any]
    patient_interview: Optional[Dict[str, Any]] = None

class AIUsageSearchRequest(BaseModel):
    configuration_id: Optional[int] = None
    user_id: Optional[int] = None
    task_type: Optional[AITaskType] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class AISummary(BaseModel):
    total_configurations: int
    active_configurations: int
    total_processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_usage: int
    total_cost: Decimal
    average_response_time: float
    success_rate: float

class AIAnalytics(BaseModel):
    total_configurations: int
    active_configurations: int
    configurations_by_provider: Dict[str, int]
    configurations_by_task_type: Dict[str, int]
    processing_job_statistics: Dict[str, int]
    usage_statistics: Dict[str, int]
    cost_statistics: Dict[str, Decimal]
    performance_metrics: Dict[str, float]
    model_performance: Dict[str, float]
    user_feedback: Dict[str, float]
