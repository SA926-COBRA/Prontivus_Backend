from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging

from app.database.database import get_db
from app.models.ai_integration import (
    AIConfiguration, AIProcessingJob, PreConsultationSummary,
    MedicalTranscription, ClinicalNotes, AIUsageLog, AIModel, AIFeedback
)
from app.models.user import User
from app.schemas.ai_integration import (
    AIConfigurationCreate, AIConfigurationUpdate, AIConfiguration as AIConfigurationSchema,
    AIProcessingJob as AIProcessingJobSchema,
    PreConsultationSummaryCreate, PreConsultationSummaryUpdate, PreConsultationSummary as PreConsultationSummarySchema,
    MedicalTranscriptionCreate, MedicalTranscriptionUpdate, MedicalTranscription as MedicalTranscriptionSchema,
    ClinicalNotesCreate, ClinicalNotesUpdate, ClinicalNotes as ClinicalNotesSchema,
    AIUsageLog as AIUsageLogSchema,
    AIModel as AIModelSchema,
    AIFeedback as AIFeedbackSchema,
    AIProcessingRequest, PreConsultationSummaryRequest,
    MedicalTranscriptionRequest, ClinicalNotesRequest,
    AIUsageSearchRequest, AISummary, AIAnalytics
)
from app.services.auth_service import AuthService
from app.services.ai_integration_service import AIIntegrationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# AI Configuration endpoints
@router.get("/configurations", response_model=List[AIConfigurationSchema], summary="Get AI configurations")
async def get_ai_configurations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    provider: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get AI configurations with filtering options"""
    try:
        service = AIIntegrationService(db)
        query = db.query(AIConfiguration)
        
        if provider:
            query = query.filter(AIConfiguration.provider == provider)
        
        if task_type:
            query = query.filter(AIConfiguration.task_type == task_type)
        
        if is_active is not None:
            query = query.filter(AIConfiguration.is_active == is_active)
        
        configurations = query.offset(skip).limit(limit).all()
        return configurations
    except Exception as e:
        logger.error(f"Error getting AI configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI configurations: {str(e)}"
        )

@router.get("/configurations/{configuration_id}", response_model=AIConfigurationSchema, summary="Get AI configuration by ID")
async def get_ai_configuration(
    configuration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI configuration by ID"""
    configuration = db.query(AIConfiguration).filter(AIConfiguration.id == configuration_id).first()
    if not configuration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI configuration not found")
    return configuration

@router.post("/configurations", response_model=AIConfigurationSchema, status_code=status.HTTP_201_CREATED, summary="Create AI configuration")
async def create_ai_configuration(
    configuration_data: AIConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI configuration"""
    try:
        service = AIIntegrationService(db)
        configuration = service.create_ai_configuration(configuration_data.dict(), current_user.id)
        return configuration
    except Exception as e:
        logger.error(f"Error creating AI configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI configuration: {str(e)}"
        )

@router.put("/configurations/{configuration_id}", response_model=AIConfigurationSchema, summary="Update AI configuration")
async def update_ai_configuration(
    configuration_id: int,
    configuration_data: AIConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an AI configuration"""
    configuration = db.query(AIConfiguration).filter(AIConfiguration.id == configuration_id).first()
    if not configuration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI configuration not found")
    
    update_data = configuration_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(configuration, field, value)
    
    db.commit()
    db.refresh(configuration)
    return configuration

# AI Processing Job endpoints
@router.get("/processing-jobs", response_model=List[AIProcessingJobSchema], summary="Get AI processing jobs")
async def get_ai_processing_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None)
):
    """Get AI processing jobs with filtering options"""
    try:
        query = db.query(AIProcessingJob)
        
        if status:
            query = query.filter(AIProcessingJob.status == status)
        
        if task_type:
            query = query.filter(AIProcessingJob.task_type == task_type)
        
        if patient_id:
            query = query.filter(AIProcessingJob.patient_id == patient_id)
        
        if doctor_id:
            query = query.filter(AIProcessingJob.doctor_id == doctor_id)
        
        jobs = query.order_by(desc(AIProcessingJob.created_at)).offset(skip).limit(limit).all()
        return jobs
    except Exception as e:
        logger.error(f"Error getting AI processing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI processing jobs: {str(e)}"
        )

@router.get("/processing-jobs/{job_id}", response_model=AIProcessingJobSchema, summary="Get AI processing job by ID")
async def get_ai_processing_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI processing job by ID"""
    job = db.query(AIProcessingJob).filter(AIProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI processing job not found")
    return job

@router.post("/processing-jobs", response_model=AIProcessingJobSchema, status_code=status.HTTP_201_CREATED, summary="Create AI processing job")
async def create_ai_processing_job(
    request: AIProcessingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI processing job"""
    try:
        service = AIIntegrationService(db)
        job = service.process_ai_request(request, current_user.id)
        return job
    except Exception as e:
        logger.error(f"Error creating AI processing job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI processing job: {str(e)}"
        )

# Pre-Consultation Summary endpoints
@router.get("/pre-consultation-summaries", response_model=List[PreConsultationSummarySchema], summary="Get pre-consultation summaries")
async def get_pre_consultation_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get pre-consultation summaries with filtering options"""
    try:
        query = db.query(PreConsultationSummary)
        
        if patient_id:
            query = query.filter(PreConsultationSummary.patient_id == patient_id)
        
        if doctor_id:
            query = query.filter(PreConsultationSummary.doctor_id == doctor_id)
        
        if status:
            query = query.filter(PreConsultationSummary.status == status)
        
        summaries = query.order_by(desc(PreConsultationSummary.created_at)).offset(skip).limit(limit).all()
        return summaries
    except Exception as e:
        logger.error(f"Error getting pre-consultation summaries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pre-consultation summaries: {str(e)}"
        )

@router.get("/pre-consultation-summaries/{summary_id}", response_model=PreConsultationSummarySchema, summary="Get pre-consultation summary by ID")
async def get_pre_consultation_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific pre-consultation summary by ID"""
    summary = db.query(PreConsultationSummary).filter(PreConsultationSummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-consultation summary not found")
    return summary

@router.post("/pre-consultation-summaries", response_model=PreConsultationSummarySchema, status_code=status.HTTP_201_CREATED, summary="Generate pre-consultation summary")
async def generate_pre_consultation_summary(
    request: PreConsultationSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new pre-consultation summary using AI"""
    try:
        service = AIIntegrationService(db)
        summary = service.generate_pre_consultation_summary(request, current_user.id)
        return summary
    except Exception as e:
        logger.error(f"Error generating pre-consultation summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pre-consultation summary: {str(e)}"
        )

@router.put("/pre-consultation-summaries/{summary_id}", response_model=PreConsultationSummarySchema, summary="Update pre-consultation summary")
async def update_pre_consultation_summary(
    summary_id: int,
    summary_data: PreConsultationSummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a pre-consultation summary"""
    summary = db.query(PreConsultationSummary).filter(PreConsultationSummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-consultation summary not found")
    
    update_data = summary_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(summary, field, value)
    
    db.commit()
    db.refresh(summary)
    return summary

# Medical Transcription endpoints
@router.get("/medical-transcriptions", response_model=List[MedicalTranscriptionSchema], summary="Get medical transcriptions")
async def get_medical_transcriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get medical transcriptions with filtering options"""
    try:
        query = db.query(MedicalTranscription)
        
        if patient_id:
            query = query.filter(MedicalTranscription.patient_id == patient_id)
        
        if doctor_id:
            query = query.filter(MedicalTranscription.doctor_id == doctor_id)
        
        if status:
            query = query.filter(MedicalTranscription.status == status)
        
        transcriptions = query.order_by(desc(MedicalTranscription.created_at)).offset(skip).limit(limit).all()
        return transcriptions
    except Exception as e:
        logger.error(f"Error getting medical transcriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical transcriptions: {str(e)}"
        )

@router.get("/medical-transcriptions/{transcription_id}", response_model=MedicalTranscriptionSchema, summary="Get medical transcription by ID")
async def get_medical_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific medical transcription by ID"""
    transcription = db.query(MedicalTranscription).filter(MedicalTranscription.id == transcription_id).first()
    if not transcription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical transcription not found")
    return transcription

@router.post("/medical-transcriptions", response_model=MedicalTranscriptionSchema, status_code=status.HTTP_201_CREATED, summary="Process medical transcription")
async def process_medical_transcription(
    request: MedicalTranscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a new medical transcription using AI"""
    try:
        service = AIIntegrationService(db)
        transcription = service.process_medical_transcription(request, current_user.id)
        return transcription
    except Exception as e:
        logger.error(f"Error processing medical transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process medical transcription: {str(e)}"
        )

@router.put("/medical-transcriptions/{transcription_id}", response_model=MedicalTranscriptionSchema, summary="Update medical transcription")
async def update_medical_transcription(
    transcription_id: int,
    transcription_data: MedicalTranscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a medical transcription"""
    transcription = db.query(MedicalTranscription).filter(MedicalTranscription.id == transcription_id).first()
    if not transcription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical transcription not found")
    
    update_data = transcription_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transcription, field, value)
    
    db.commit()
    db.refresh(transcription)
    return transcription

# Clinical Notes endpoints
@router.get("/clinical-notes", response_model=List[ClinicalNotesSchema], summary="Get clinical notes")
async def get_clinical_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get clinical notes with filtering options"""
    try:
        query = db.query(ClinicalNotes)
        
        if patient_id:
            query = query.filter(ClinicalNotes.patient_id == patient_id)
        
        if doctor_id:
            query = query.filter(ClinicalNotes.doctor_id == doctor_id)
        
        if status:
            query = query.filter(ClinicalNotes.status == status)
        
        notes = query.order_by(desc(ClinicalNotes.created_at)).offset(skip).limit(limit).all()
        return notes
    except Exception as e:
        logger.error(f"Error getting clinical notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get clinical notes: {str(e)}"
        )

@router.get("/clinical-notes/{notes_id}", response_model=ClinicalNotesSchema, summary="Get clinical notes by ID")
async def get_clinical_notes_by_id(
    notes_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific clinical notes by ID"""
    notes = db.query(ClinicalNotes).filter(ClinicalNotes.id == notes_id).first()
    if not notes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical notes not found")
    return notes

@router.post("/clinical-notes", response_model=ClinicalNotesSchema, status_code=status.HTTP_201_CREATED, summary="Generate clinical notes")
async def generate_clinical_notes(
    request: ClinicalNotesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate new clinical notes using AI"""
    try:
        service = AIIntegrationService(db)
        notes = service.generate_clinical_notes(request, current_user.id)
        return notes
    except Exception as e:
        logger.error(f"Error generating clinical notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate clinical notes: {str(e)}"
        )

@router.put("/clinical-notes/{notes_id}", response_model=ClinicalNotesSchema, summary="Update clinical notes")
async def update_clinical_notes(
    notes_id: int,
    notes_data: ClinicalNotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update clinical notes"""
    notes = db.query(ClinicalNotes).filter(ClinicalNotes.id == notes_id).first()
    if not notes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical notes not found")
    
    update_data = notes_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notes, field, value)
    
    db.commit()
    db.refresh(notes)
    return notes

# AI Usage Log endpoints
@router.get("/usage-logs", response_model=List[AIUsageLogSchema], summary="Get AI usage logs")
async def get_ai_usage_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    configuration_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    task_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get AI usage logs with filtering options"""
    try:
        service = AIIntegrationService(db)
        request = AIUsageSearchRequest(
            configuration_id=configuration_id,
            user_id=user_id,
            task_type=task_type,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        logs = service.get_ai_usage_logs(request)
        return logs
    except Exception as e:
        logger.error(f"Error getting AI usage logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI usage logs: {str(e)}"
        )

# Summary and Analytics endpoints
@router.get("/summary", response_model=AISummary, summary="Get AI summary")
async def get_ai_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI usage summary statistics"""
    try:
        service = AIIntegrationService(db)
        summary = service.get_ai_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI summary: {str(e)}"
        )

@router.get("/analytics", response_model=AIAnalytics, summary="Get AI analytics")
async def get_ai_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed AI analytics"""
    try:
        service = AIIntegrationService(db)
        analytics = service.get_ai_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting AI analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI analytics: {str(e)}"
        )

# Health check endpoint
@router.get("/health", summary="AI integration service health check")
async def health_check():
    """Check the health of the AI Integration service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai_integration",
        "features": {
            "pre_consultation_summary": True,
            "medical_transcription": True,
            "clinical_notes": True,
            "ai_configurations": True,
            "usage_analytics": True
        }
    }
