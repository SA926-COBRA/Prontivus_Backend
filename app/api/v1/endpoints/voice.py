from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import base64

from app.database.database import get_db
from app.models.voice import VoiceSession, VoiceTranscription, ClinicalVoiceNote, VoiceProcessingJob
from app.models.user import User
from app.schemas.voice import (
    VoiceSessionStartRequest, VoiceSessionStartResponse,
    VoiceAudioUploadRequest, VoiceAudioUploadResponse,
    VoiceTranscriptionRequest, VoiceTranscriptionResponse,
    VoiceNoteGenerationRequest, VoiceNoteGenerationResponse,
    VoiceSessionEndRequest, VoiceSessionEndResponse,
    VoiceSession as VoiceSessionSchema,
    VoiceTranscription as VoiceTranscriptionSchema,
    ClinicalVoiceNote as ClinicalVoiceNoteSchema,
    VoiceProcessingJob as VoiceProcessingJobSchema,
    VoiceDashboardStats, VoiceAnalyticsSummary,
    VoiceProcessingStatus
)
from app.services.auth_service import AuthService
from app.services.voice_service import VoiceProcessingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Voice Session endpoints
@router.post("/sessions/start", response_model=VoiceSessionStartResponse, status_code=status.HTTP_201_CREATED, summary="Start a new voice recording session")
async def start_voice_session(
    request: VoiceSessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new voice recording session for clinical progress notes"""
    try:
        voice_service = VoiceProcessingService(db)
        session = voice_service.start_voice_session(request, current_user.id)
        
        return VoiceSessionStartResponse(
            session_id=session.session_id,
            status=session.status.value,
            message="Voice session started successfully"
        )
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start voice session: {str(e)}"
        )

@router.post("/sessions/{session_id}/upload", response_model=VoiceAudioUploadResponse, summary="Upload audio data to voice session")
async def upload_audio_to_session(
    session_id: str,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload audio data to an existing voice session"""
    try:
        # Read audio file data
        audio_data = await audio_file.read()
        audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Determine audio format from file extension
        audio_format = audio_file.filename.split('.')[-1].lower() if audio_file.filename else 'wav'
        
        request = VoiceAudioUploadRequest(
            session_id=session_id,
            audio_data=audio_data_b64,
            audio_format=audio_format
        )
        
        voice_service = VoiceProcessingService(db)
        result = voice_service.upload_audio(request, current_user.id)
        
        return VoiceAudioUploadResponse(
            success=result["success"],
            message=result["message"],
            file_path=result.get("file_path"),
            file_size=result.get("file_size")
        )
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}"
        )

@router.post("/sessions/{session_id}/transcribe", response_model=VoiceTranscriptionResponse, summary="Transcribe audio from voice session")
async def transcribe_session_audio(
    session_id: str,
    request: VoiceTranscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio from a voice session"""
    try:
        # Ensure session_id matches
        request.session_id = session_id
        
        voice_service = VoiceProcessingService(db)
        result = voice_service.transcribe_audio(request, current_user.id)
        
        return VoiceTranscriptionResponse(
            success=result["success"],
            message=result["message"],
            transcription_id=result.get("transcription_id"),
            estimated_processing_time=result.get("estimated_processing_time")
        )
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe audio: {str(e)}"
        )

@router.post("/sessions/{session_id}/generate-note", response_model=VoiceNoteGenerationResponse, summary="Generate clinical note from voice session")
async def generate_clinical_note(
    session_id: str,
    request: VoiceNoteGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a clinical note from a voice session transcription"""
    try:
        # Ensure session_id matches
        request.session_id = session_id
        
        voice_service = VoiceProcessingService(db)
        result = voice_service.generate_clinical_note(request, current_user.id)
        
        return VoiceNoteGenerationResponse(
            success=result["success"],
            message=result["message"],
            note_id=result.get("note_id"),
            estimated_processing_time=result.get("estimated_processing_time")
        )
    except Exception as e:
        logger.error(f"Error generating clinical note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate clinical note: {str(e)}"
        )

@router.post("/sessions/{session_id}/end", response_model=VoiceSessionEndResponse, summary="End a voice recording session")
async def end_voice_session(
    session_id: str,
    request: VoiceSessionEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a voice recording session"""
    try:
        voice_service = VoiceProcessingService(db)
        result = voice_service.end_voice_session(
            session_id, 
            current_user.id, 
            request.auto_transcribe, 
            request.auto_generate_note
        )
        
        return VoiceSessionEndResponse(
            success=result["success"],
            message=result["message"],
            session_duration=result.get("session_duration"),
            transcription_job_id=result.get("transcription_job_id"),
            note_generation_job_id=result.get("note_generation_job_id")
        )
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end voice session: {str(e)}"
        )

@router.get("/sessions", response_model=List[VoiceSessionSchema], summary="Get user's voice sessions")
async def get_voice_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None)
):
    """Get user's voice sessions with filtering options"""
    query = db.query(VoiceSession).filter(VoiceSession.created_by == current_user.id)
    
    if status:
        query = query.filter(VoiceSession.status == status)
    
    if patient_id:
        query = query.filter(VoiceSession.patient_id == patient_id)
    
    sessions = query.order_by(VoiceSession.created_at.desc()).offset(skip).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=VoiceSessionSchema, summary="Get voice session by ID")
async def get_voice_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific voice session by ID"""
    session = db.query(VoiceSession).filter(
        VoiceSession.session_id == session_id,
        VoiceSession.created_by == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice session not found")
    
    return session

@router.get("/sessions/{session_id}/status", response_model=VoiceProcessingStatus, summary="Get voice session processing status")
async def get_voice_session_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processing status for a voice session"""
    try:
        voice_service = VoiceProcessingService(db)
        status = voice_service.get_processing_status(session_id)
        return status
    except Exception as e:
        logger.error(f"Error getting voice session status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session status: {str(e)}"
        )

# Voice Transcription endpoints
@router.get("/transcriptions", response_model=List[VoiceTranscriptionSchema], summary="Get voice transcriptions")
async def get_voice_transcriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session_id: Optional[str] = Query(None)
):
    """Get voice transcriptions with filtering options"""
    query = db.query(VoiceTranscription)
    
    if session_id:
        # Find session by session_id and filter transcriptions
        session = db.query(VoiceSession).filter(
            VoiceSession.session_id == session_id,
            VoiceSession.created_by == current_user.id
        ).first()
        
        if session:
            query = query.filter(VoiceTranscription.session_id == session.id)
        else:
            # Return empty list if session not found or not owned by user
            return []
    
    transcriptions = query.order_by(VoiceTranscription.created_at.desc()).offset(skip).limit(limit).all()
    return transcriptions

@router.get("/transcriptions/{transcription_id}", response_model=VoiceTranscriptionSchema, summary="Get voice transcription by ID")
async def get_voice_transcription(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific voice transcription by ID"""
    transcription = db.query(VoiceTranscription).join(VoiceSession).filter(
        VoiceTranscription.id == transcription_id,
        VoiceSession.created_by == current_user.id
    ).first()
    
    if not transcription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice transcription not found")
    
    return transcription

# Clinical Voice Note endpoints
@router.get("/notes", response_model=List[ClinicalVoiceNoteSchema], summary="Get clinical voice notes")
async def get_clinical_voice_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session_id: Optional[str] = Query(None),
    note_type: Optional[str] = Query(None)
):
    """Get clinical voice notes with filtering options"""
    query = db.query(ClinicalVoiceNote).join(VoiceSession).filter(
        VoiceSession.created_by == current_user.id
    )
    
    if session_id:
        session = db.query(VoiceSession).filter(
            VoiceSession.session_id == session_id,
            VoiceSession.created_by == current_user.id
        ).first()
        
        if session:
            query = query.filter(ClinicalVoiceNote.session_id == session.id)
        else:
            return []
    
    if note_type:
        query = query.filter(ClinicalVoiceNote.note_type == note_type)
    
    notes = query.order_by(ClinicalVoiceNote.created_at.desc()).offset(skip).limit(limit).all()
    return notes

@router.get("/notes/{note_id}", response_model=ClinicalVoiceNoteSchema, summary="Get clinical voice note by ID")
async def get_clinical_voice_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific clinical voice note by ID"""
    note = db.query(ClinicalVoiceNote).join(VoiceSession).filter(
        ClinicalVoiceNote.id == note_id,
        VoiceSession.created_by == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical voice note not found")
    
    return note

@router.put("/notes/{note_id}/review", response_model=ClinicalVoiceNoteSchema, summary="Review and approve clinical voice note")
async def review_clinical_voice_note(
    note_id: int,
    approved: bool,
    doctor_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and approve/reject a clinical voice note"""
    note = db.query(ClinicalVoiceNote).join(VoiceSession).filter(
        ClinicalVoiceNote.id == note_id,
        VoiceSession.created_by == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical voice note not found")
    
    # Update review status
    note.reviewed_by_doctor = True
    note.reviewed_at = datetime.utcnow()
    note.approved_by_doctor = approved
    note.approved_at = datetime.utcnow() if approved else None
    note.doctor_notes = doctor_notes
    
    db.commit()
    db.refresh(note)
    
    return note

# Voice Processing Job endpoints
@router.get("/jobs", response_model=List[VoiceProcessingJobSchema], summary="Get voice processing jobs")
async def get_voice_processing_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None)
):
    """Get voice processing jobs with filtering options"""
    query = db.query(VoiceProcessingJob).join(VoiceSession).filter(
        VoiceSession.created_by == current_user.id
    )
    
    if status:
        query = query.filter(VoiceProcessingJob.status == status)
    
    if job_type:
        query = query.filter(VoiceProcessingJob.job_type == job_type)
    
    jobs = query.order_by(VoiceProcessingJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@router.get("/jobs/{job_id}", response_model=VoiceProcessingJobSchema, summary="Get voice processing job by ID")
async def get_voice_processing_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific voice processing job by ID"""
    job = db.query(VoiceProcessingJob).join(VoiceSession).filter(
        VoiceProcessingJob.job_id == job_id,
        VoiceSession.created_by == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice processing job not found")
    
    return job

# Analytics and Dashboard endpoints
@router.get("/dashboard", response_model=VoiceDashboardStats, summary="Get voice processing dashboard statistics")
async def get_voice_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get voice processing dashboard statistics"""
    try:
        # This would contain actual dashboard queries
        # For now, returning mock data
        
        stats = VoiceDashboardStats(
            active_sessions=0,
            total_sessions_today=0,
            total_duration_today_minutes=0.0,
            average_session_duration_minutes=0.0,
            transcription_success_rate=0.0,
            average_audio_quality=0.0,
            pending_transcriptions=0,
            completed_notes_today=0,
            most_active_doctors=[],
            recent_sessions=[]
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting voice dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard statistics: {str(e)}"
        )

@router.get("/analytics", response_model=VoiceAnalyticsSummary, summary="Get voice processing analytics")
async def get_voice_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get voice processing analytics and metrics"""
    try:
        # This would contain actual analytics queries
        # For now, returning mock data
        
        analytics = VoiceAnalyticsSummary(
            total_sessions=0,
            total_duration_hours=0.0,
            total_transcriptions=0,
            total_notes_generated=0,
            average_audio_quality=0.0,
            average_transcription_confidence=0.0,
            error_rate=0.0,
            most_used_specialties=[],
            usage_trends=[],
            quality_metrics={}
        )
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting voice analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

# Health check endpoint
@router.get("/health", summary="Voice processing service health check")
async def health_check():
    """Check the health of the voice processing service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "voice_processing",
        "features": {
            "whisper_available": True,
            "google_speech_available": True,
            "audio_processing_available": True
        }
    }
