"""
Enhanced Telemedicine API Endpoints
Native video consultation platform with WebRTC support
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from app.database.database import get_db
from app.services.native_telemedicine_service import NativeTelemedicineService
from app.services.auth_service import AuthService
from app.schemas.telemedicine import (
    TelemedicineSessionCreate, TelemedicineSessionUpdate, TelemedicineSession,
    TelemedicineMessageCreate, TelemedicineMessage,
    TelemedicineFileCreate, TelemedicineFile,
    TelemedicineConsentCreate, TelemedicineConsent,
    TelemedicineConfigurationCreate, TelemedicineConfigurationUpdate, TelemedicineConfiguration,
    TelemedicineAnalytics, TelemedicineSessionJoin,
    TelemedicineSessionStatus, TelemedicineConsentStatus
)

router = APIRouter()
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str, participant_id: str):
        await websocket.accept()
        connection_key = f"{session_id}_{participant_id}"
        self.active_connections[connection_key] = websocket

    def disconnect(self, session_id: str, participant_id: str):
        connection_key = f"{session_id}_{participant_id}"
        if connection_key in self.active_connections:
            del self.active_connections[connection_key]

    async def send_personal_message(self, message: str, session_id: str, participant_id: str):
        connection_key = f"{session_id}_{participant_id}"
        if connection_key in self.active_connections:
            websocket = self.active_connections[connection_key]
            await websocket.send_text(message)

    async def broadcast_to_session(self, message: str, session_id: str, exclude_participant: str = None):
        for connection_key, websocket in self.active_connections.items():
            if connection_key.startswith(f"{session_id}_") and connection_key != f"{session_id}_{exclude_participant}":
                await websocket.send_text(message)

manager = ConnectionManager()

# Session Management Endpoints
@router.post("/sessions", response_model=TelemedicineSession)
async def create_session(
    session_data: TelemedicineSessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new telemedicine session"""
    try:
        service = NativeTelemedicineService(db)
        return service.create_session(session_data, current_user.id)
    except Exception as e:
        logger.error(f"Error creating telemedicine session: {e}")
        raise HTTPException(status_code=500, detail="Error creating telemedicine session")

@router.get("/sessions", response_model=List[TelemedicineSession])
async def get_sessions(
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[TelemedicineSessionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get telemedicine sessions with filters"""
    try:
        query = db.query(TelemedicineSession)
        
        if doctor_id:
            query = query.filter(TelemedicineSession.doctor_id == doctor_id)
        if patient_id:
            query = query.filter(TelemedicineSession.patient_id == patient_id)
        if status:
            query = query.filter(TelemedicineSession.status == status)
        
        sessions = query.order_by(TelemedicineSession.scheduled_start.desc()).offset(skip).limit(limit).all()
        return [TelemedicineSession.from_orm(session) for session in sessions]
    except Exception as e:
        logger.error(f"Error getting telemedicine sessions: {e}")
        raise HTTPException(status_code=500, detail="Error getting telemedicine sessions")

@router.get("/sessions/{session_id}", response_model=TelemedicineSession)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get telemedicine session by ID"""
    try:
        service = NativeTelemedicineService(db)
        session = service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Telemedicine session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting telemedicine session: {e}")
        raise HTTPException(status_code=500, detail="Error getting telemedicine session")

@router.get("/sessions/patient-link/{token}", response_model=TelemedicineSession)
async def get_session_by_patient_link(
    token: str,
    db: Session = Depends(get_db)
):
    """Get session by patient link token (public endpoint)"""
    try:
        service = NativeTelemedicineService(db)
        session = service.get_session_by_patient_link(token)
        if not session:
            raise HTTPException(status_code=404, detail="Invalid or expired patient link")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session by patient link: {e}")
        raise HTTPException(status_code=500, detail="Error getting session by patient link")

# Session Control Endpoints
@router.post("/sessions/{session_id}/join")
async def join_session(
    session_id: str,
    join_data: TelemedicineSessionJoin,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Join a telemedicine session"""
    try:
        service = NativeTelemedicineService(db)
        result = service.join_session(join_data)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining session: {e}")
        raise HTTPException(status_code=500, detail="Error joining session")

@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Start a telemedicine session"""
    try:
        service = NativeTelemedicineService(db)
        result = service.start_session(session_id, current_user.id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Error starting session")

@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """End a telemedicine session"""
    try:
        service = NativeTelemedicineService(db)
        result = service.end_session(session_id, current_user.id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail="Error ending session")

# WebRTC Signaling Endpoint
@router.post("/sessions/{session_id}/signaling")
async def handle_webrtc_signaling(
    session_id: str,
    signaling_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Handle WebRTC signaling messages"""
    try:
        service = NativeTelemedicineService(db)
        result = service.handle_webrtc_signaling(session_id, signaling_data)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling WebRTC signaling: {e}")
        raise HTTPException(status_code=500, detail="Error handling WebRTC signaling")

# Chat Endpoints
@router.post("/sessions/{session_id}/messages", response_model=TelemedicineMessage)
async def send_message(
    session_id: str,
    message_data: TelemedicineMessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Send a chat message"""
    try:
        service = NativeTelemedicineService(db)
        return service.send_message(session_id, message_data)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Error sending message")

@router.get("/sessions/{session_id}/messages", response_model=List[TelemedicineMessage])
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get messages for a session"""
    try:
        service = NativeTelemedicineService(db)
        return service.get_session_messages(session_id)
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail="Error getting session messages")

# File Sharing Endpoints
@router.post("/sessions/{session_id}/files", response_model=TelemedicineFile)
async def upload_file(
    session_id: str,
    file_data: TelemedicineFileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Upload a file to session"""
    try:
        service = NativeTelemedicineService(db)
        return service.upload_file(session_id, file_data)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Error uploading file")

# Consent Management Endpoints
@router.post("/sessions/{session_id}/consent", response_model=TelemedicineConsent)
async def request_consent(
    session_id: str,
    consent_data: TelemedicineConsentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Request patient consent for recording or screen sharing"""
    try:
        service = NativeTelemedicineService(db)
        return service.request_consent(session_id, consent_data)
    except Exception as e:
        logger.error(f"Error requesting consent: {e}")
        raise HTTPException(status_code=500, detail="Error requesting consent")

@router.post("/consent/{consent_id}/respond")
async def respond_to_consent(
    consent_id: int,
    granted: bool,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Respond to consent request"""
    try:
        service = NativeTelemedicineService(db)
        return service.respond_to_consent(consent_id, granted, current_user.id)
    except Exception as e:
        logger.error(f"Error responding to consent: {e}")
        raise HTTPException(status_code=500, detail="Error responding to consent")

# Analytics Endpoints
@router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get analytics for a session"""
    try:
        service = NativeTelemedicineService(db)
        return service.get_session_analytics(session_id)
    except Exception as e:
        logger.error(f"Error getting session analytics: {e}")
        raise HTTPException(status_code=500, detail="Error getting session analytics")

@router.get("/sessions/active")
async def get_active_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get all active sessions"""
    try:
        service = NativeTelemedicineService(db)
        return service.get_active_sessions()
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail="Error getting active sessions")

# Configuration Endpoints
@router.get("/configuration", response_model=TelemedicineConfiguration)
async def get_configuration(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get telemedicine configuration"""
    try:
        service = NativeTelemedicineService(db)
        return service.get_configuration()
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail="Error getting configuration")

@router.put("/configuration", response_model=TelemedicineConfiguration)
async def update_configuration(
    config_data: TelemedicineConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Update telemedicine configuration"""
    try:
        service = NativeTelemedicineService(db)
        return service.update_configuration(config_data)
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")

# WebSocket Endpoint for Real-time Communication
@router.websocket("/ws/{session_id}/{participant_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    participant_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id, participant_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "webrtc_signaling":
                # Forward WebRTC signaling to target participant
                target_participant = message["target"]
                await manager.send_personal_message(
                    json.dumps(message),
                    session_id,
                    target_participant
                )
            
            elif message["type"] == "chat_message":
                # Broadcast chat message to all participants
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    participant_id
                )
            
            elif message["type"] == "screen_sharing":
                # Broadcast screen sharing status
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    participant_id
                )
            
            elif message["type"] == "recording_status":
                # Broadcast recording status
                await manager.broadcast_to_session(
                    json.dumps(message),
                    session_id,
                    participant_id
                )
            
            else:
                # Unknown message type
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Unknown message type"
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(session_id, participant_id)
        # Notify other participants about disconnection
        await manager.broadcast_to_session(
            json.dumps({
                "type": "participant_left",
                "participant_id": participant_id,
                "timestamp": datetime.utcnow().isoformat()
            }),
            session_id
        )
