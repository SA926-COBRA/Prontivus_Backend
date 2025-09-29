"""
Enhanced AI Integration API Endpoints
Audio-based pre-consultation with transcription and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from app.database.database import get_db
from app.services.audio_based_ai_service import AudioBasedAIService
from app.services.auth_service import AuthService
from app.schemas.ai_integration import (
    AIAnalysisSessionCreate, AIAnalysisSessionUpdate, AIAnalysisSession,
    AIAnalysisCreate, AIAnalysisUpdate, AIAnalysis,
    AIConfigurationCreate, AIConfigurationUpdate, AIConfiguration,
    AIUsageAnalytics, AIPromptTemplateCreate, AIPromptTemplateUpdate, AIPromptTemplate,
    AIAnalysisRequest, AIAnalysisResponse, AIAnalysisResult,
    AITranscriptionResult, AIClinicalSummaryResult, AIDiagnosisSuggestionResult,
    AIExamSuggestionResult, AITreatmentSuggestionResult, AIPrescriptionSuggestionResult,
    AIProvider, AIAnalysisStatus, AIAnalysisType
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Session Management Endpoints
@router.post("/sessions", response_model=AIAnalysisSession)
async def create_analysis_session(
    session_data: AIAnalysisSessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new AI analysis session"""
    try:
        service = AudioBasedAIService(db)
        return service.create_analysis_session(session_data, current_user.id)
    except Exception as e:
        logger.error(f"Error creating AI analysis session: {e}")
        raise HTTPException(status_code=500, detail="Error creating AI analysis session")

@router.get("/sessions", response_model=List[AIAnalysisSession])
async def get_analysis_sessions(
    doctor_id: Optional[int] = None,
    status: Optional[AIAnalysisStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get AI analysis sessions with filters"""
    try:
        query = db.query(AIAnalysisSession)
        
        if doctor_id:
            query = query.filter(AIAnalysisSession.doctor_id == doctor_id)
        if status:
            query = query.filter(AIAnalysisSession.status == status)
        
        sessions = query.order_by(AIAnalysisSession.created_at.desc()).offset(skip).limit(limit).all()
        return [AIAnalysisSession.from_orm(session) for session in sessions]
    except Exception as e:
        logger.error(f"Error getting AI analysis sessions: {e}")
        raise HTTPException(status_code=500, detail="Error getting AI analysis sessions")

@router.get("/sessions/{session_id}", response_model=AIAnalysisSession)
async def get_analysis_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get AI analysis session by ID"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="AI analysis session not found")
        
        return AIAnalysisSession.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI analysis session: {e}")
        raise HTTPException(status_code=500, detail="Error getting AI analysis session")

# Audio Recording Endpoints
@router.post("/sessions/{session_id}/start-recording")
async def start_audio_recording(
    session_id: str,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Start audio recording for a session"""
    try:
        service = AudioBasedAIService(db)
        
        # Read audio file
        audio_data = await audio_file.read()
        audio_format = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'webm'
        
        result = service.start_audio_recording(session_id, audio_data, audio_format)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting audio recording: {e}")
        raise HTTPException(status_code=500, detail="Error starting audio recording")

@router.post("/sessions/{session_id}/stop-recording")
async def stop_audio_recording(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Stop audio recording for a session"""
    try:
        service = AudioBasedAIService(db)
        result = service.stop_audio_recording(session_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping audio recording: {e}")
        raise HTTPException(status_code=500, detail="Error stopping audio recording")

# Transcription Endpoints
@router.post("/sessions/{session_id}/transcribe")
async def transcribe_audio(
    session_id: str,
    provider: AIProvider = AIProvider.OPENAI,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Transcribe audio using AI service"""
    try:
        service = AudioBasedAIService(db)
        result = await service.transcribe_audio(session_id, provider)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail="Error transcribing audio")

@router.get("/sessions/{session_id}/transcription")
async def get_transcription(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get transcription for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        transcription = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.TRANSCRIPTION,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not transcription:
            raise HTTPException(status_code=404, detail="No transcription found")
        
        return {
            "text": transcription.output_data.get("text", ""),
            "language": transcription.output_data.get("language", ""),
            "confidence": transcription.confidence_score,
            "duration": transcription.output_data.get("duration", 0),
            "segments": transcription.output_data.get("segments", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcription: {e}")
        raise HTTPException(status_code=500, detail="Error getting transcription")

# AI Analysis Endpoints
@router.post("/sessions/{session_id}/analyze")
async def analyze_transcription(
    session_id: str,
    analysis_type: AIAnalysisType,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Analyze transcription and generate medical insights"""
    try:
        service = AudioBasedAIService(db)
        result = await service.analyze_transcription(session_id, analysis_type)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transcription: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing transcription")

@router.get("/sessions/{session_id}/clinical-summary")
async def get_clinical_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get clinical summary for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        summary = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.CLINICAL_SUMMARY,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="No clinical summary found")
        
        return {
            "summary": summary.output_data.get("summary", ""),
            "structured_data": summary.output_data.get("structured_data", {}),
            "confidence": summary.confidence_score,
            "word_count": summary.output_data.get("word_count", 0),
            "summary_length": summary.output_data.get("summary_length", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clinical summary: {e}")
        raise HTTPException(status_code=500, detail="Error getting clinical summary")

@router.get("/sessions/{session_id}/diagnosis-suggestions")
async def get_diagnosis_suggestions(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get diagnosis suggestions for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        diagnosis = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.DIAGNOSIS_SUGGESTION,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not diagnosis:
            raise HTTPException(status_code=404, detail="No diagnosis suggestions found")
        
        return {
            "diagnoses": diagnosis.output_data.get("diagnoses", []),
            "total_suggestions": diagnosis.output_data.get("total_suggestions", 0),
            "confidence": diagnosis.confidence_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagnosis suggestions: {e}")
        raise HTTPException(status_code=500, detail="Error getting diagnosis suggestions")

@router.get("/sessions/{session_id}/exam-suggestions")
async def get_exam_suggestions(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get exam suggestions for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        exams = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.EXAM_SUGGESTION,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not exams:
            raise HTTPException(status_code=404, detail="No exam suggestions found")
        
        return {
            "exams": exams.output_data.get("exams", []),
            "total_suggestions": exams.output_data.get("total_suggestions", 0),
            "confidence": exams.confidence_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam suggestions: {e}")
        raise HTTPException(status_code=500, detail="Error getting exam suggestions")

@router.get("/sessions/{session_id}/treatment-suggestions")
async def get_treatment_suggestions(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get treatment suggestions for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        treatments = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.TREATMENT_SUGGESTION,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not treatments:
            raise HTTPException(status_code=404, detail="No treatment suggestions found")
        
        return {
            "treatments": treatments.output_data.get("treatments", []),
            "total_suggestions": treatments.output_data.get("total_suggestions", 0),
            "confidence": treatments.confidence_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting treatment suggestions: {e}")
        raise HTTPException(status_code=500, detail="Error getting treatment suggestions")

@router.get("/sessions/{session_id}/icd-coding")
async def get_icd_coding(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get ICD-10 coding suggestions for a session"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        icd_coding = db.query(AIAnalysis).filter(
            and_(
                AIAnalysis.session_id == session.id,
                AIAnalysis.analysis_type == AIAnalysisType.ICD_CODING,
                AIAnalysis.status == AIAnalysisStatus.COMPLETED
            )
        ).first()
        
        if not icd_coding:
            raise HTTPException(status_code=404, detail="No ICD coding found")
        
        return {
            "codes": icd_coding.output_data.get("codes", []),
            "total_codes": icd_coding.output_data.get("total_codes", 0),
            "confidence": icd_coding.confidence_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ICD coding: {e}")
        raise HTTPException(status_code=500, detail="Error getting ICD coding")

# Analytics Endpoints
@router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get analytics for an AI analysis session"""
    try:
        service = AudioBasedAIService(db)
        return service.get_session_analytics(session_id)
    except Exception as e:
        logger.error(f"Error getting session analytics: {e}")
        raise HTTPException(status_code=500, detail="Error getting session analytics")

# Configuration Endpoints
@router.get("/configuration", response_model=AIConfiguration)
async def get_configuration(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get AI configuration"""
    try:
        service = AudioBasedAIService(db)
        return service.get_configuration()
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail="Error getting configuration")

@router.put("/configuration", response_model=AIConfiguration)
async def update_configuration(
    config_data: AIConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Update AI configuration"""
    try:
        service = AudioBasedAIService(db)
        return service.update_configuration(config_data)
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")

# Consent Management
@router.post("/sessions/{session_id}/consent")
async def give_recording_consent(
    session_id: str,
    consent_given: bool = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Give consent for audio recording"""
    try:
        session = db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.recording_consent_given = consent_given
        session.recording_consent_timestamp = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "consent_given": consent_given,
            "timestamp": session.recording_consent_timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error giving recording consent: {e}")
        raise HTTPException(status_code=500, detail="Error giving recording consent")

# Batch Analysis Endpoint
@router.post("/sessions/{session_id}/full-analysis")
async def perform_full_analysis(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Perform complete analysis: transcription + all analysis types"""
    try:
        service = AudioBasedAIService(db)
        
        # Step 1: Transcribe audio
        transcription_result = await service.transcribe_audio(session_id)
        if not transcription_result["success"]:
            return {"success": False, "error": "Transcription failed", "step": "transcription"}
        
        # Step 2: Perform all analyses
        analyses = [
            AIAnalysisType.CLINICAL_SUMMARY,
            AIAnalysisType.DIAGNOSIS_SUGGESTION,
            AIAnalysisType.EXAM_SUGGESTION,
            AIAnalysisType.TREATMENT_SUGGESTION,
            AIAnalysisType.ICD_CODING
        ]
        
        results = {"transcription": transcription_result}
        
        for analysis_type in analyses:
            try:
                result = await service.analyze_transcription(session_id, analysis_type)
                results[analysis_type.value] = result
            except Exception as e:
                logger.error(f"Error in {analysis_type} analysis: {e}")
                results[analysis_type.value] = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "results": results,
            "message": "Full analysis completed"
        }
        
    except Exception as e:
        logger.error(f"Error performing full analysis: {e}")
        raise HTTPException(status_code=500, detail="Error performing full analysis")
