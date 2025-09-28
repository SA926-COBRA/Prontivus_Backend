"""
AI Integration Schemas
Pydantic schemas for AI-powered medical consultation analysis
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"


class AIAnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIAnalysisType(str, Enum):
    TRANSCRIPTION = "transcription"
    CLINICAL_SUMMARY = "clinical_summary"
    DIAGNOSIS_SUGGESTION = "diagnosis_suggestion"
    EXAM_SUGGESTION = "exam_suggestion"
    TREATMENT_SUGGESTION = "treatment_suggestion"
    ICD_CODING = "icd_coding"
    PRESCRIPTION_SUGGESTION = "prescription_suggestion"


# Base schemas
class AIAnalysisSessionBase(BaseModel):
    consultation_id: Optional[int] = None
    telemedicine_session_id: Optional[int] = None
    doctor_id: int
    patient_id: int
    audio_file_path: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    ai_provider: AIProvider = AIProvider.OPENAI
    ai_model: str = "gpt-4"
    language: str = "pt-BR"
    enabled_analyses: Optional[List[AIAnalysisType]] = None
    custom_prompts: Optional[Dict[str, str]] = None
    patient_consent_given: bool = False
    data_retention_days: int = 30


class AIAnalysisSessionCreate(AIAnalysisSessionBase):
    pass


class AIAnalysisSessionUpdate(BaseModel):
    status: Optional[AIAnalysisStatus] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AIAnalysisSession(AIAnalysisSessionBase):
    id: int
    tenant_id: int
    session_id: str
    audio_file_size_mb: Optional[float] = None
    video_file_path: Optional[str] = None
    status: AIAnalysisStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    consent_given_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIAnalysisBase(BaseModel):
    analysis_type: AIAnalysisType
    analysis_version: str = "1.0"
    input_text: Optional[str] = None
    input_audio_segment_start: Optional[int] = None
    input_audio_segment_end: Optional[int] = None
    ai_provider: AIProvider
    ai_model: str
    prompt_used: Optional[str] = None


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysisUpdate(BaseModel):
    raw_result: Optional[str] = None
    processed_result: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    status: Optional[AIAnalysisStatus] = None
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    doctor_reviewed: Optional[bool] = None
    doctor_approved: Optional[bool] = None
    doctor_notes: Optional[str] = None
    doctor_modified_result: Optional[Dict[str, Any]] = None


class AIAnalysis(AIAnalysisBase):
    id: int
    session_id: int
    raw_result: Optional[str] = None
    processed_result: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    status: AIAnalysisStatus
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    doctor_reviewed: bool
    doctor_approved: Optional[bool] = None
    doctor_notes: Optional[str] = None
    doctor_modified_result: Optional[Dict[str, Any]] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIConfigurationBase(BaseModel):
    is_enabled: bool = False
    default_provider: AIProvider = AIProvider.OPENAI
    default_model: str = "gpt-4"
    default_language: str = "pt-BR"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None
    enabled_analyses: Optional[List[AIAnalysisType]] = None
    transcription_enabled: bool = True
    clinical_summary_enabled: bool = True
    diagnosis_suggestion_enabled: bool = True
    exam_suggestion_enabled: bool = True
    treatment_suggestion_enabled: bool = True
    icd_coding_enabled: bool = True
    prescription_suggestion_enabled: bool = True
    min_confidence_threshold: float = Field(0.7, ge=0, le=1)
    max_analysis_duration_minutes: int = 60
    auto_approve_low_risk: bool = False
    monthly_budget_usd: Optional[float] = None
    cost_per_analysis_usd: Optional[float] = None
    alert_threshold_percent: int = Field(80, ge=1, le=100)
    data_retention_days: int = 30
    auto_delete_enabled: bool = True
    anonymize_data: bool = True
    lgpd_compliant: bool = True
    integrate_with_emr: bool = True
    auto_populate_notes: bool = False
    require_doctor_approval: bool = True
    custom_prompts: Optional[Dict[str, str]] = None
    notify_on_completion: bool = True
    notify_on_error: bool = True
    notify_on_budget_alert: bool = True


class AIConfigurationCreate(AIConfigurationBase):
    pass


class AIConfigurationUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    default_provider: Optional[AIProvider] = None
    default_model: Optional[str] = None
    default_language: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None
    enabled_analyses: Optional[List[AIAnalysisType]] = None
    transcription_enabled: Optional[bool] = None
    clinical_summary_enabled: Optional[bool] = None
    diagnosis_suggestion_enabled: Optional[bool] = None
    exam_suggestion_enabled: Optional[bool] = None
    treatment_suggestion_enabled: Optional[bool] = None
    icd_coding_enabled: Optional[bool] = None
    prescription_suggestion_enabled: Optional[bool] = None
    min_confidence_threshold: Optional[float] = Field(None, ge=0, le=1)
    max_analysis_duration_minutes: Optional[int] = None
    auto_approve_low_risk: Optional[bool] = None
    monthly_budget_usd: Optional[float] = None
    cost_per_analysis_usd: Optional[float] = None
    alert_threshold_percent: Optional[int] = Field(None, ge=1, le=100)
    data_retention_days: Optional[int] = None
    auto_delete_enabled: Optional[bool] = None
    anonymize_data: Optional[bool] = None
    lgpd_compliant: Optional[bool] = None
    integrate_with_emr: Optional[bool] = None
    auto_populate_notes: Optional[bool] = None
    require_doctor_approval: Optional[bool] = None
    custom_prompts: Optional[Dict[str, str]] = None
    notify_on_completion: Optional[bool] = None
    notify_on_error: Optional[bool] = None
    notify_on_budget_alert: Optional[bool] = None


class AIConfiguration(AIConfigurationBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Specialized schemas for API requests
class AIAnalysisRequest(BaseModel):
    """Request to start AI analysis"""
    session_id: str
    analysis_types: List[AIAnalysisType]
    audio_file_path: Optional[str] = None
    custom_prompts: Optional[Dict[str, str]] = None


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis"""
    success: bool
    session_id: str
    analysis_id: Optional[int] = None
    status: AIAnalysisStatus
    message: Optional[str] = None
    estimated_completion_time: Optional[int] = None  # Seconds


class AIAnalysisResult(BaseModel):
    """Structured AI analysis result"""
    analysis_type: AIAnalysisType
    result: Dict[str, Any]
    confidence_score: float
    processing_time_seconds: int
    tokens_used: int
    cost_usd: float


class AITranscriptionResult(BaseModel):
    """Transcription analysis result"""
    text: str
    segments: List[Dict[str, Any]]  # Time-stamped segments
    speakers: List[Dict[str, Any]]  # Speaker identification
    confidence_score: float
    language_detected: str


class AIClinicalSummaryResult(BaseModel):
    """Clinical summary analysis result"""
    chief_complaint: str
    history_of_present_illness: str
    review_of_systems: str
    physical_examination: str
    assessment_and_plan: str
    confidence_score: float


class AIDiagnosisSuggestionResult(BaseModel):
    """Diagnosis suggestion analysis result"""
    primary_diagnosis: str
    differential_diagnoses: List[Dict[str, Any]]
    icd_codes: List[str]
    confidence_score: float
    reasoning: str


class AIExamSuggestionResult(BaseModel):
    """Exam suggestion analysis result"""
    suggested_exams: List[Dict[str, Any]]
    urgency_level: str  # low, medium, high
    reasoning: str
    confidence_score: float


class AITreatmentSuggestionResult(BaseModel):
    """Treatment suggestion analysis result"""
    treatment_options: List[Dict[str, Any]]
    medication_suggestions: List[Dict[str, Any]]
    follow_up_recommendations: List[str]
    confidence_score: float
    reasoning: str


class AIPrescriptionSuggestionResult(BaseModel):
    """Prescription suggestion analysis result"""
    suggested_medications: List[Dict[str, Any]]
    dosages: List[Dict[str, Any]]
    contraindications: List[str]
    drug_interactions: List[str]
    confidence_score: float


# Analytics schemas
class AIUsageAnalyticsBase(BaseModel):
    date: datetime
    period_type: str = "daily"
    total_sessions: int = 0
    total_analyses: int = 0
    total_audio_minutes: float = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0
    average_cost_per_session: float = 0
    average_cost_per_analysis: float = 0
    average_confidence_score: float = 0
    doctor_approval_rate: float = 0
    auto_approval_rate: float = 0


class AIUsageAnalyticsCreate(AIUsageAnalyticsBase):
    pass


class AIUsageAnalytics(AIUsageAnalyticsBase):
    id: int
    tenant_id: int
    transcription_count: int = 0
    clinical_summary_count: int = 0
    diagnosis_suggestion_count: int = 0
    exam_suggestion_count: int = 0
    treatment_suggestion_count: int = 0
    icd_coding_count: int = 0
    prescription_suggestion_count: int = 0
    openai_usage_count: int = 0
    anthropic_usage_count: int = 0
    google_usage_count: int = 0
    azure_usage_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard schemas
class AIDashboardResponse(BaseModel):
    """AI dashboard response"""
    total_sessions: int
    active_sessions: int
    completed_sessions_today: int
    total_analyses: int
    average_confidence_score: float
    doctor_approval_rate: float
    monthly_cost_usd: float
    monthly_budget_used_percent: float
    most_used_analysis_types: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]


class AISessionSummary(BaseModel):
    """Summary of an AI analysis session"""
    id: int
    session_id: str
    doctor_name: str
    patient_name: str
    status: str
    analysis_types: List[str]
    confidence_score: Optional[float] = None
    cost_usd: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AISessionsResponse(BaseModel):
    """Response with list of AI analysis sessions"""
    sessions: List[AISessionSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int


# Prompt template schemas
class AIPromptTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    analysis_type: AIAnalysisType
    language: str = "pt-BR"
    version: str = "1.0"
    system_prompt: str = Field(..., min_length=1)
    user_prompt_template: str = Field(..., min_length=1)
    output_format: Optional[Dict[str, Any]] = None
    is_default: bool = False
    is_active: bool = True
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, ge=1, le=4000)


class AIPromptTemplateCreate(AIPromptTemplateBase):
    pass


class AIPromptTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    system_prompt: Optional[str] = Field(None, min_length=1)
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    output_format: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)


class AIPromptTemplate(AIPromptTemplateBase):
    id: int
    tenant_id: int
    usage_count: int = 0
    success_rate: float = 0
    average_confidence: float = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True