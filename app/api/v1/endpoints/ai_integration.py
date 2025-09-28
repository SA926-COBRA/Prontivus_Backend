"""
AI Integration API Endpoints
API endpoints for AI-powered medical consultation analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.services.ai_integration_service import AIService
from app.schemas.ai_integration import (
    AIAnalysisSession, AIAnalysisSessionCreate, AIAnalysisSessionUpdate,
    AIAnalysis, AIAnalysisCreate, AIAnalysisUpdate,
    AIConfiguration, AIConfigurationCreate, AIConfigurationUpdate,
    AIDashboardResponse, AISessionsResponse,
    AIAnalysisRequest, AIAnalysisResponse
)
from app.services.auth_service import AuthService

router = APIRouter()


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """Get AI service instance"""
    return AIService(db)


def get_tenant_id(request: Request) -> int:
    """Extract tenant ID from request (simplified for now)"""
    return 1  # Default tenant ID


# Session Management Endpoints
@router.get("/sessions", response_model=AISessionsResponse)
async def get_analysis_sessions(
    status: Optional[str] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    request: Request = None,
    ai_service: AIService = Depends(get_ai_service)
):
    """Get AI analysis sessions with pagination"""
    try:
        tenant_id = get_tenant_id(request)
        sessions_response = ai_service.get_analysis_sessions(
            tenant_id=tenant_id,
            status=status,
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size
        )
        return sessions_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.post("/sessions", response_model=AIAnalysisSession, status_code=status.HTTP_201_CREATED)
async def create_analysis_session(
    session_data: AIAnalysisSessionCreate,
    request: Request = None,
    ai_service: AIService = Depends(get_ai_service)
):
    """Create a new AI analysis session"""
    try:
        tenant_id = get_tenant_id(request)
        session = ai_service.create_analysis_session(tenant_id, session_data)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=AIAnalysisSession)
async def get_analysis_session(
    session_id: str,
    ai_service: AIService = Depends(get_ai_service)
):
    """Get AI analysis session by session ID"""
    session = ai_service.get_analysis_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post("/sessions/{session_id}/start", response_model=AIAnalysisResponse)
async def start_analysis(
    session_id: str,
    analysis_request: AIAnalysisRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Start AI analysis for a session"""
    result = ai_service.start_analysis(session_id, analysis_request.analysis_types)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result


# Configuration Endpoints
@router.get("/configuration", response_model=AIConfiguration)
async def get_configuration(
    request: Request = None,
    ai_service: AIService = Depends(get_ai_service)
):
    """Get AI configuration for the current tenant"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = ai_service.get_configuration(tenant_id)
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI configuration not found"
            )
        return configuration
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/configuration", response_model=AIConfiguration, status_code=status.HTTP_201_CREATED)
async def create_or_update_configuration(
    config_data: AIConfigurationCreate,
    request: Request = None,
    ai_service: AIService = Depends(get_ai_service)
):
    """Create or update AI configuration"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = ai_service.create_or_update_configuration(tenant_id, config_data)
        return configuration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update configuration: {str(e)}"
        )


# Dashboard Endpoints
@router.get("/dashboard", response_model=AIDashboardResponse)
async def get_dashboard_data(
    request: Request = None,
    ai_service: AIService = Depends(get_ai_service)
):
    """Get AI dashboard data"""
    try:
        tenant_id = get_tenant_id(request)
        dashboard_data = ai_service.get_dashboard_data(tenant_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for AI integration service"""
    return {
        "status": "healthy",
        "service": "ai-integration",
        "timestamp": datetime.now().isoformat()
    }