from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging
import json

from app.database.database import get_db
from app.models.integrations import (
    HealthPlanIntegration, TelemedicineIntegration, TelemedicineSession,
    IntegrationSyncLog, HealthPlanAuthorization, IntegrationWebhook,
    WebhookLog, IntegrationHealthCheck
)
from app.models.user import User
from app.schemas.integrations import (
    HealthPlanIntegrationCreate, HealthPlanIntegrationUpdate, HealthPlanIntegration as HealthPlanIntegrationSchema,
    TelemedicineIntegrationCreate, TelemedicineIntegrationUpdate, TelemedicineIntegration as TelemedicineIntegrationSchema,
    TelemedicineSessionCreate, TelemedicineSessionUpdate, TelemedicineSession as TelemedicineSessionSchema,
    IntegrationSyncLog as IntegrationSyncLogSchema,
    HealthPlanAuthorizationCreate, HealthPlanAuthorizationUpdate, HealthPlanAuthorization as HealthPlanAuthorizationSchema,
    IntegrationWebhook as IntegrationWebhookSchema,
    WebhookLog as WebhookLogSchema,
    IntegrationHealthCheck as IntegrationHealthCheckSchema,
    IntegrationSearchRequest, TelemedicineSessionSearchRequest,
    AuthorizationSearchRequest, IntegrationSyncRequest,
    TelemedicineSessionRequest, AuthorizationRequest,
    IntegrationSummary, IntegrationAnalytics
)
from app.services.auth_service import AuthService
from app.services.integrations_service import IntegrationsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Health Plan Integration endpoints
@router.get("/health-plan", response_model=List[HealthPlanIntegrationSchema], summary="Get health plan integrations")
async def get_health_plan_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    integration_name: Optional[str] = Query(None),
    integration_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get health plan integrations with filtering options"""
    try:
        service = IntegrationsService(db)
        request = IntegrationSearchRequest(
            integration_name=integration_name,
            integration_type=integration_type,
            status=status,
            created_by=created_by,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        integrations = service.search_health_plan_integrations(request)
        return integrations
    except Exception as e:
        logger.error(f"Error getting health plan integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health plan integrations: {str(e)}"
        )

@router.get("/health-plan/{integration_id}", response_model=HealthPlanIntegrationSchema, summary="Get health plan integration by ID")
async def get_health_plan_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific health plan integration by ID"""
    integration = db.query(HealthPlanIntegration).filter(HealthPlanIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan integration not found")
    return integration

@router.post("/health-plan", response_model=HealthPlanIntegrationSchema, status_code=status.HTTP_201_CREATED, summary="Create health plan integration")
async def create_health_plan_integration(
    integration_data: HealthPlanIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new health plan integration"""
    try:
        service = IntegrationsService(db)
        integration = service.create_health_plan_integration(integration_data.dict(), current_user.id)
        return integration
    except Exception as e:
        logger.error(f"Error creating health plan integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health plan integration: {str(e)}"
        )

@router.put("/health-plan/{integration_id}", response_model=HealthPlanIntegrationSchema, summary="Update health plan integration")
async def update_health_plan_integration(
    integration_id: int,
    integration_data: HealthPlanIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a health plan integration"""
    integration = db.query(HealthPlanIntegration).filter(HealthPlanIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan integration not found")
    
    update_data = integration_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)
    
    db.commit()
    db.refresh(integration)
    return integration

@router.post("/health-plan/{integration_id}/test", summary="Test health plan integration")
async def test_health_plan_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test health plan integration connectivity"""
    try:
        service = IntegrationsService(db)
        result = service.test_health_plan_integration(integration_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing health plan integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test health plan integration: {str(e)}"
        )

@router.post("/health-plan/{integration_id}/sync", response_model=IntegrationSyncLogSchema, summary="Sync health plan data")
async def sync_health_plan_data(
    integration_id: int,
    request: IntegrationSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync data with health plan integration"""
    try:
        request.integration_id = integration_id
        service = IntegrationsService(db)
        sync_log = service.sync_health_plan_data(request)
        return sync_log
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing health plan data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync health plan data: {str(e)}"
        )

# Telemedicine Integration endpoints
@router.get("/telemedicine", response_model=List[TelemedicineIntegrationSchema], summary="Get telemedicine integrations")
async def get_telemedicine_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    integration_name: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get telemedicine integrations with filtering options"""
    try:
        service = IntegrationsService(db)
        request = IntegrationSearchRequest(
            integration_name=integration_name,
            provider=provider,
            status=status,
            created_by=created_by,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        integrations = service.search_telemedicine_integrations(request)
        return integrations
    except Exception as e:
        logger.error(f"Error getting telemedicine integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get telemedicine integrations: {str(e)}"
        )

@router.get("/telemedicine/{integration_id}", response_model=TelemedicineIntegrationSchema, summary="Get telemedicine integration by ID")
async def get_telemedicine_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific telemedicine integration by ID"""
    integration = db.query(TelemedicineIntegration).filter(TelemedicineIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine integration not found")
    return integration

@router.post("/telemedicine", response_model=TelemedicineIntegrationSchema, status_code=status.HTTP_201_CREATED, summary="Create telemedicine integration")
async def create_telemedicine_integration(
    integration_data: TelemedicineIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new telemedicine integration"""
    try:
        service = IntegrationsService(db)
        integration = service.create_telemedicine_integration(integration_data.dict(), current_user.id)
        return integration
    except Exception as e:
        logger.error(f"Error creating telemedicine integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create telemedicine integration: {str(e)}"
        )

@router.put("/telemedicine/{integration_id}", response_model=TelemedicineIntegrationSchema, summary="Update telemedicine integration")
async def update_telemedicine_integration(
    integration_id: int,
    integration_data: TelemedicineIntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a telemedicine integration"""
    integration = db.query(TelemedicineIntegration).filter(TelemedicineIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine integration not found")
    
    update_data = integration_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)
    
    db.commit()
    db.refresh(integration)
    return integration

@router.post("/telemedicine/{integration_id}/test", summary="Test telemedicine integration")
async def test_telemedicine_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test telemedicine integration connectivity"""
    try:
        service = IntegrationsService(db)
        result = service.test_telemedicine_integration(integration_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing telemedicine integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test telemedicine integration: {str(e)}"
        )

# Telemedicine Session endpoints
@router.get("/telemedicine/sessions", response_model=List[TelemedicineSessionSchema], summary="Get telemedicine sessions")
async def get_telemedicine_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    integration_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """Get telemedicine sessions with filtering options"""
    try:
        service = IntegrationsService(db)
        request = TelemedicineSessionSearchRequest(
            integration_id=integration_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        sessions = service.search_telemedicine_sessions(request)
        return sessions
    except Exception as e:
        logger.error(f"Error getting telemedicine sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get telemedicine sessions: {str(e)}"
        )

@router.get("/telemedicine/sessions/{session_id}", response_model=TelemedicineSessionSchema, summary="Get telemedicine session by ID")
async def get_telemedicine_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific telemedicine session by ID"""
    session = db.query(TelemedicineSession).filter(TelemedicineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found")
    return session

@router.post("/telemedicine/sessions", response_model=TelemedicineSessionSchema, status_code=status.HTTP_201_CREATED, summary="Create telemedicine session")
async def create_telemedicine_session(
    session_data: TelemedicineSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new telemedicine session"""
    try:
        service = IntegrationsService(db)
        session = service.create_telemedicine_session(session_data, current_user.id)
        return session
    except Exception as e:
        logger.error(f"Error creating telemedicine session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create telemedicine session: {str(e)}"
        )

@router.put("/telemedicine/sessions/{session_id}", response_model=TelemedicineSessionSchema, summary="Update telemedicine session")
async def update_telemedicine_session(
    session_id: int,
    session_data: TelemedicineSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a telemedicine session"""
    session = db.query(TelemedicineSession).filter(TelemedicineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found")
    
    update_data = session_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    return session

@router.post("/telemedicine/sessions/{session_id}/start", response_model=TelemedicineSessionSchema, summary="Start telemedicine session")
async def start_telemedicine_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a telemedicine session"""
    try:
        service = IntegrationsService(db)
        session = service.start_telemedicine_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting telemedicine session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start telemedicine session: {str(e)}"
        )

@router.post("/telemedicine/sessions/{session_id}/end", response_model=TelemedicineSessionSchema, summary="End telemedicine session")
async def end_telemedicine_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a telemedicine session"""
    try:
        service = IntegrationsService(db)
        session = service.end_telemedicine_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error ending telemedicine session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end telemedicine session: {str(e)}"
        )

# Health Plan Authorization endpoints
@router.get("/authorizations", response_model=List[HealthPlanAuthorizationSchema], summary="Get health plan authorizations")
async def get_health_plan_authorizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    integration_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    authorization_status: Optional[str] = Query(None),
    procedure_code: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get health plan authorizations with filtering options"""
    try:
        service = IntegrationsService(db)
        request = AuthorizationSearchRequest(
            integration_id=integration_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            authorization_status=authorization_status,
            procedure_code=procedure_code,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        authorizations = service.search_authorizations(request)
        return authorizations
    except Exception as e:
        logger.error(f"Error getting health plan authorizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health plan authorizations: {str(e)}"
        )

@router.get("/authorizations/{authorization_id}", response_model=HealthPlanAuthorizationSchema, summary="Get health plan authorization by ID")
async def get_health_plan_authorization(
    authorization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific health plan authorization by ID"""
    authorization = db.query(HealthPlanAuthorization).filter(HealthPlanAuthorization.id == authorization_id).first()
    if not authorization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan authorization not found")
    return authorization

@router.post("/authorizations", response_model=HealthPlanAuthorizationSchema, status_code=status.HTTP_201_CREATED, summary="Create health plan authorization")
async def create_health_plan_authorization(
    authorization_data: AuthorizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new health plan authorization request"""
    try:
        service = IntegrationsService(db)
        authorization = service.create_authorization_request(authorization_data, current_user.id)
        return authorization
    except Exception as e:
        logger.error(f"Error creating health plan authorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health plan authorization: {str(e)}"
        )

@router.put("/authorizations/{authorization_id}", response_model=HealthPlanAuthorizationSchema, summary="Update health plan authorization")
async def update_health_plan_authorization(
    authorization_id: int,
    authorization_data: HealthPlanAuthorizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a health plan authorization"""
    authorization = db.query(HealthPlanAuthorization).filter(HealthPlanAuthorization.id == authorization_id).first()
    if not authorization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan authorization not found")
    
    update_data = authorization_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(authorization, field, value)
    
    db.commit()
    db.refresh(authorization)
    return authorization

# Webhook endpoints
@router.get("/webhooks", response_model=List[IntegrationWebhookSchema], summary="Get integration webhooks")
async def get_integration_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get integration webhooks"""
    webhooks = db.query(IntegrationWebhook).offset(skip).limit(limit).all()
    return webhooks

@router.get("/webhooks/{webhook_id}", response_model=IntegrationWebhookSchema, summary="Get integration webhook by ID")
async def get_integration_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific integration webhook by ID"""
    webhook = db.query(IntegrationWebhook).filter(IntegrationWebhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration webhook not found")
    return webhook

@router.post("/webhooks", response_model=IntegrationWebhookSchema, status_code=status.HTTP_201_CREATED, summary="Create integration webhook")
async def create_integration_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new integration webhook"""
    try:
        service = IntegrationsService(db)
        webhook = service.create_webhook(webhook_data, current_user.id)
        return webhook
    except Exception as e:
        logger.error(f"Error creating integration webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration webhook: {str(e)}"
        )

@router.post("/webhooks/{webhook_id}/process", response_model=WebhookLogSchema, summary="Process webhook event")
async def process_webhook_event(
    webhook_id: int,
    event_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a webhook event"""
    try:
        service = IntegrationsService(db)
        webhook_log = service.process_webhook(webhook_id, event_data)
        return webhook_log
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook event: {str(e)}"
        )

# Health Check endpoints
@router.post("/health-check/{integration_id}", response_model=IntegrationHealthCheckSchema, summary="Perform integration health check")
async def perform_integration_health_check(
    integration_id: int,
    check_type: str = Query("connectivity", description="Type of health check to perform"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform health check on integration"""
    try:
        service = IntegrationsService(db)
        health_check = service.perform_health_check(integration_id, check_type)
        return health_check
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing integration health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform integration health check: {str(e)}"
        )

# Summary endpoints
@router.get("/summary", response_model=IntegrationSummary, summary="Get integration summary")
async def get_integration_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get integration summary statistics"""
    try:
        service = IntegrationsService(db)
        summary = service.get_integration_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting integration summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration summary: {str(e)}"
        )

@router.get("/analytics", response_model=IntegrationAnalytics, summary="Get integration analytics")
async def get_integration_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed integration analytics"""
    try:
        service = IntegrationsService(db)
        analytics = service.get_integration_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting integration analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration analytics: {str(e)}"
        )

# WebSocket endpoint for real-time updates
@router.websocket("/ws/{integration_id}")
async def websocket_endpoint(websocket: WebSocket, integration_id: int):
    """WebSocket endpoint for real-time integration updates"""
    await websocket.accept()
    try:
        while True:
            # Send periodic updates about integration status
            # In real implementation, this would send actual status updates
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "integration_id": integration_id,
                "status": "active",
                "timestamp": datetime.utcnow().isoformat()
            }))
            await asyncio.sleep(30)  # Send update every 30 seconds
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for integration {integration_id}")

# Health check endpoint
@router.get("/health", summary="Integrations service health check")
async def health_check():
    """Check the health of the Integrations service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "integrations",
        "features": {
            "health_plan_integrations": True,
            "telemedicine_integrations": True,
            "authorization_management": True,
            "webhook_processing": True,
            "real_time_updates": True
        }
    }
