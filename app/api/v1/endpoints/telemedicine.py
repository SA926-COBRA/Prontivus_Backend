"""
Telemedicine API Endpoints
API endpoints for native telemedicine video platform
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.services.telemedicine_service import TelemedicineService
from app.schemas.telemedicine import (
    TelemedicineSession, TelemedicineSessionCreate, TelemedicineSessionUpdate,
    TelemedicineMessage, TelemedicineMessageCreate,
    TelemedicineFile, TelemedicineFileCreate,
    TelemedicineConsent, TelemedicineConsentCreate, TelemedicineConsentUpdate,
    TelemedicineConfiguration, TelemedicineConfigurationCreate, TelemedicineConfigurationUpdate,
    TelemedicineAnalytics, TelemedicineAnalyticsCreate,
    TelemedicineDashboardResponse, TelemedicineSessionsResponse,
    TelemedicineSessionJoin, TelemedicineSessionJoinResponse,
    TelemedicineSessionStart, TelemedicineSessionEnd,
    TelemedicineConsentRequest, TelemedicineConsentResponse
)
from app.core.auth import get_current_user

router = APIRouter()


def get_telemedicine_service(db: Session = Depends(get_db)) -> TelemedicineService:
    """Get telemedicine service instance"""
    return TelemedicineService(db)


def get_tenant_id(request: Request) -> int:
    """Extract tenant ID from request (simplified for now)"""
    # In a real implementation, this would come from JWT token or request context
    return 1  # Default tenant ID


# Session Management Endpoints
@router.get("/sessions", response_model=TelemedicineSessionsResponse)
async def get_sessions(
    status: Optional[str] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    request: Request = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get telemedicine sessions with pagination"""
    try:
        tenant_id = get_tenant_id(request)
        sessions_response = telemedicine_service.get_sessions(
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


@router.post("/sessions", response_model=TelemedicineSession, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: TelemedicineSessionCreate,
    request: Request = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Create a new telemedicine session"""
    try:
        tenant_id = get_tenant_id(request)
        session = telemedicine_service.create_session(tenant_id, session_data)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=TelemedicineSession)
async def get_session(
    session_id: str,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get telemedicine session by session ID"""
    session = telemedicine_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.put("/sessions/{session_id}", response_model=TelemedicineSession)
async def update_session(
    session_id: str,
    session_data: TelemedicineSessionUpdate,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Update telemedicine session"""
    session = telemedicine_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    updated_session = telemedicine_service.update_session(session.id, session_data)
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )
    return updated_session


@router.post("/sessions/{session_id}/start", response_model=TelemedicineSession)
async def start_session(
    session_id: str,
    start_data: TelemedicineSessionStart,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Start a telemedicine session"""
    session = telemedicine_service.start_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be started"
        )
    return session


@router.post("/sessions/{session_id}/end", response_model=TelemedicineSession)
async def end_session(
    session_id: str,
    end_data: TelemedicineSessionEnd,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """End a telemedicine session"""
    session = telemedicine_service.end_session(session_id, end_data.reason)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or cannot be ended"
        )
    return session


@router.post("/sessions/{session_id}/join", response_model=TelemedicineSessionJoinResponse)
async def join_session(
    session_id: str,
    join_data: TelemedicineSessionJoin,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Join a telemedicine session"""
    result = telemedicine_service.join_session(
        session_id, 
        join_data.participant_type, 
        join_data.participant_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return TelemedicineSessionJoinResponse(**result)


# Message Endpoints
@router.get("/sessions/{session_id}/messages", response_model=List[TelemedicineMessage])
async def get_messages(
    session_id: str,
    limit: int = 50,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get messages for a telemedicine session"""
    messages = telemedicine_service.get_messages(session_id, limit)
    return messages


@router.post("/sessions/{session_id}/messages", response_model=TelemedicineMessage, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: str,
    message_data: TelemedicineMessageCreate,
    sender_id: int,
    sender_type: str = "doctor",
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Send a message in a telemedicine session"""
    try:
        message = telemedicine_service.send_message(session_id, message_data, sender_id, sender_type)
        return message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


# Consent Management Endpoints
@router.post("/sessions/{session_id}/consent", response_model=TelemedicineConsent, status_code=status.HTTP_201_CREATED)
async def create_consent_request(
    session_id: str,
    consent_data: TelemedicineConsentCreate,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Create a consent request for a session"""
    try:
        consent = telemedicine_service.create_consent_request(session_id, consent_data)
        return consent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consent request: {str(e)}"
        )


@router.put("/consent/{consent_id}/grant", response_model=TelemedicineConsentResponse)
async def grant_consent(
    consent_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Grant consent for a telemedicine session"""
    consent = telemedicine_service.grant_consent(consent_id, ip_address, user_agent)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found or cannot be granted"
        )
    
    return TelemedicineConsentResponse(
        consent_id=consent.id,
        granted=consent.granted,
        granted_at=consent.granted_at,
        ip_address=consent.ip_address,
        user_agent=consent.user_agent
    )


# Configuration Endpoints
@router.get("/configuration", response_model=TelemedicineConfiguration)
async def get_configuration(
    request: Request = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get telemedicine configuration for the current tenant"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = telemedicine_service.get_configuration(tenant_id)
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Telemedicine configuration not found"
            )
        return configuration
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/configuration", response_model=TelemedicineConfiguration, status_code=status.HTTP_201_CREATED)
async def create_or_update_configuration(
    config_data: TelemedicineConfigurationCreate,
    request: Request = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Create or update telemedicine configuration"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = telemedicine_service.create_or_update_configuration(tenant_id, config_data)
        return configuration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update configuration: {str(e)}"
        )


# Dashboard and Analytics Endpoints
@router.get("/dashboard", response_model=TelemedicineDashboardResponse)
async def get_dashboard_data(
    request: Request = None,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get telemedicine dashboard data"""
    try:
        tenant_id = get_tenant_id(request)
        dashboard_data = telemedicine_service.get_dashboard_data(tenant_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


# File Management Endpoints (simplified for now)
@router.post("/sessions/{session_id}/files", response_model=TelemedicineFile, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session_id: str,
    file_data: TelemedicineFileCreate,
    uploaded_by: int,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Upload a file to a telemedicine session"""
    try:
        # In a real implementation, this would handle file upload and encryption
        # For now, return a mock response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="File upload not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/sessions/{session_id}/files", response_model=List[TelemedicineFile])
async def get_session_files(
    session_id: str,
    telemedicine_service: TelemedicineService = Depends(get_telemedicine_service)
):
    """Get files for a telemedicine session"""
    try:
        # In a real implementation, this would return actual files
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get files: {str(e)}"
        )


# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for telemedicine service"""
    return {
        "status": "healthy",
        "service": "telemedicine",
        "timestamp": datetime.now().isoformat()
    }
