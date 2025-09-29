"""
Native Telemedicine WebRTC Service
Handles WebRTC connections, signaling, and media management
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import jwt
from cryptography.fernet import Fernet

from app.models.telemedicine import (
    TelemedicineSession, TelemedicineMessage, TelemedicineFile, 
    TelemedicineConsent, TelemedicineConfiguration, TelemedicineAnalytics,
    TelemedicineSessionStatus, TelemedicineConsentStatus
)
from app.schemas.telemedicine import (
    TelemedicineSessionCreate, TelemedicineSessionUpdate, TelemedicineSession,
    TelemedicineMessageCreate, TelemedicineMessage,
    TelemedicineFileCreate, TelemedicineFile,
    TelemedicineConsentCreate, TelemedicineConsent,
    TelemedicineConfigurationCreate, TelemedicineConfigurationUpdate, TelemedicineConfiguration,
    TelemedicineAnalytics, TelemedicineSessionJoin
)

logger = logging.getLogger(__name__)


class NativeTelemedicineService:
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.signaling_servers: List[Dict[str, str]] = [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
            {"urls": "stun:stun2.l.google.com:19302"}
        ]

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{uuid.uuid4().hex[:16]}"

    def _generate_patient_link(self, session_id: str) -> str:
        """Generate secure patient link"""
        token_data = {
            "session_id": session_id,
            "exp": datetime.utcnow() + timedelta(hours=24),  # 24 hour expiration
            "iat": datetime.utcnow()
        }
        token = jwt.encode(token_data, "telemedicine_secret", algorithm="HS256")
        return f"/telemedicine/join/{token}"

    def _verify_patient_link(self, token: str) -> Optional[str]:
        """Verify patient link token and return session_id"""
        try:
            payload = jwt.decode(token, "telemedicine_secret", algorithms=["HS256"])
            return payload.get("session_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # Session Management
    def create_session(self, session_data: TelemedicineSessionCreate, user_id: int) -> TelemedicineSession:
        """Create a new telemedicine session"""
        try:
            session_id = self._generate_session_id()
            patient_link = self._generate_patient_link(session_id)
            
            session_dict = session_data.dict()
            session_dict['session_id'] = session_id
            session_dict['patient_link'] = patient_link
            session_dict['patient_link_expires'] = datetime.utcnow() + timedelta(hours=24)
            session_dict['status'] = TelemedicineSessionStatus.SCHEDULED
            
            # Set default WebRTC configuration
            session_dict['webrtc_config'] = {
                "iceServers": self.signaling_servers,
                "iceCandidatePoolSize": 10
            }
            session_dict['stun_servers'] = self.signaling_servers
            session_dict['turn_servers'] = []  # Add TURN servers if needed
            
            session = TelemedicineSession(**session_dict)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            # Initialize session in memory
            self.active_sessions[session_id] = {
                "session": session,
                "participants": {},
                "messages": [],
                "files": [],
                "recording": None,
                "screen_sharing": False,
                "chat_enabled": session.chat_enabled,
                "recording_enabled": session.recording_enabled
            }
            
            return TelemedicineSession.from_orm(session)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating telemedicine session: {e}")
            raise

    def get_session_by_id(self, session_id: str) -> Optional[TelemedicineSession]:
        """Get telemedicine session by ID"""
        session = self.db.query(TelemedicineSession).filter(
            TelemedicineSession.session_id == session_id
        ).first()
        return TelemedicineSession.from_orm(session) if session else None

    def get_session_by_patient_link(self, token: str) -> Optional[TelemedicineSession]:
        """Get session by patient link token"""
        session_id = self._verify_patient_link(token)
        if not session_id:
            return None
        return self.get_session_by_id(session_id)

    def join_session(self, join_data: TelemedicineSessionJoin) -> Dict[str, Any]:
        """Join a telemedicine session"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == join_data.session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Check if session is active
            if session.status not in [TelemedicineSessionStatus.SCHEDULED, TelemedicineSessionStatus.WAITING]:
                return {"success": False, "error": "Session is not available"}
            
            # Check participant limits
            if len(self.active_sessions.get(join_data.session_id, {}).get("participants", {})) >= session.max_participants:
                return {"success": False, "error": "Session is full"}
            
            # Initialize session if not already active
            if join_data.session_id not in self.active_sessions:
                self.active_sessions[join_data.session_id] = {
                    "session": session,
                    "participants": {},
                    "messages": [],
                    "files": [],
                    "recording": None,
                    "screen_sharing": False,
                    "chat_enabled": session.chat_enabled,
                    "recording_enabled": session.recording_enabled
                }
            
            # Add participant
            participant_id = f"{join_data.participant_type}_{join_data.participant_id}"
            self.active_sessions[join_data.session_id]["participants"][participant_id] = {
                "type": join_data.participant_type,
                "id": join_data.participant_id,
                "joined_at": datetime.utcnow(),
                "status": "connected"
            }
            
            # Update session status
            if session.status == TelemedicineSessionStatus.SCHEDULED:
                session.status = TelemedicineSessionStatus.WAITING
                session.actual_start = datetime.utcnow()
                self.db.commit()
            
            return {
                "success": True,
                "session": TelemedicineSession.from_orm(session),
                "webrtc_config": session.webrtc_config,
                "participants": list(self.active_sessions[join_data.session_id]["participants"].keys())
            }
            
        except Exception as e:
            logger.error(f"Error joining session: {e}")
            return {"success": False, "error": str(e)}

    def start_session(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """Start a telemedicine session"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if session.status != TelemedicineSessionStatus.WAITING:
                return {"success": False, "error": "Session is not in waiting state"}
            
            # Check if doctor is present
            doctor_present = any(
                p["type"] == "doctor" for p in 
                self.active_sessions.get(session_id, {}).get("participants", {}).values()
            )
            
            if not doctor_present:
                return {"success": False, "error": "Doctor must be present to start session"}
            
            # Start session
            session.status = TelemedicineSessionStatus.IN_PROGRESS
            session.actual_start = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": True,
                "session": TelemedicineSession.from_orm(session),
                "message": "Session started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return {"success": False, "error": str(e)}

    def end_session(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """End a telemedicine session"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if session.status != TelemedicineSessionStatus.IN_PROGRESS:
                return {"success": False, "error": "Session is not in progress"}
            
            # End session
            session.status = TelemedicineSessionStatus.COMPLETED
            session.actual_end = datetime.utcnow()
            
            # Calculate duration
            if session.actual_start:
                duration = (session.actual_end - session.actual_start).total_seconds()
                session.recording_duration = int(duration)
            
            self.db.commit()
            
            # Clean up active session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return {
                "success": True,
                "session": TelemedicineSession.from_orm(session),
                "message": "Session ended successfully"
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {"success": False, "error": str(e)}

    # WebRTC Signaling
    def handle_webrtc_signaling(self, session_id: str, signaling_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebRTC signaling messages"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session_info = self.active_sessions[session_id]
            
            # Store signaling data
            if "signaling" not in session_info:
                session_info["signaling"] = []
            
            session_info["signaling"].append({
                "from": signaling_data.from_participant,
                "to": signaling_data.to_participant,
                "type": signaling_data.message_type,
                "data": signaling_data.data,
                "timestamp": datetime.utcnow()
            })
            
            # Forward to target participant
            return {
                "success": True,
                "message": "Signaling data forwarded",
                "target": signaling_data.to_participant
            }
            
        except Exception as e:
            logger.error(f"Error handling WebRTC signaling: {e}")
            return {"success": False, "error": str(e)}

    # Chat Management
    def send_message(self, session_id: str, message_data: TelemedicineMessageCreate) -> TelemedicineMessage:
        """Send a chat message"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            if not session.chat_enabled:
                raise ValueError("Chat is disabled for this session")
            
            message_dict = message_data.dict()
            message_dict['session_id'] = session.id
            message_dict['timestamp'] = datetime.utcnow()
            
            message = TelemedicineMessage(**message_dict)
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # Add to active session
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["messages"].append({
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "sender_type": message.sender_type,
                    "content": message.content,
                    "message_type": message.message_type,
                    "timestamp": message.timestamp.isoformat()
                })
            
            return TelemedicineMessage.from_orm(message)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending message: {e}")
            raise

    def get_session_messages(self, session_id: str) -> List[TelemedicineMessage]:
        """Get messages for a session"""
        session = self.db.query(TelemedicineSession).filter(
            TelemedicineSession.session_id == session_id
        ).first()
        
        if not session:
            return []
        
        messages = self.db.query(TelemedicineMessage).filter(
            TelemedicineMessage.session_id == session.id
        ).order_by(TelemedicineMessage.timestamp).all()
        
        return [TelemedicineMessage.from_orm(msg) for msg in messages]

    # File Sharing
    def upload_file(self, session_id: str, file_data: TelemedicineFileCreate) -> TelemedicineFile:
        """Upload a file to session"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            file_dict = file_data.dict()
            file_dict['session_id'] = session.id
            file_dict['uploaded_at'] = datetime.utcnow()
            
            file = TelemedicineFile(**file_dict)
            self.db.add(file)
            self.db.commit()
            self.db.refresh(file)
            
            # Add to active session
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["files"].append({
                    "id": file.id,
                    "filename": file.filename,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "uploaded_by": file.uploaded_by,
                    "uploaded_at": file.uploaded_at.isoformat()
                })
            
            return TelemedicineFile.from_orm(file)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error uploading file: {e}")
            raise

    # Consent Management
    def request_consent(self, session_id: str, consent_data: TelemedicineConsentCreate) -> TelemedicineConsent:
        """Request patient consent for recording or screen sharing"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            consent_dict = consent_data.dict()
            consent_dict['session_id'] = session.id
            consent_dict['status'] = TelemedicineConsentStatus.PENDING
            consent_dict['requested_at'] = datetime.utcnow()
            
            consent = TelemedicineConsent(**consent_dict)
            self.db.add(consent)
            self.db.commit()
            self.db.refresh(consent)
            
            return TelemedicineConsent.from_orm(consent)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error requesting consent: {e}")
            raise

    def respond_to_consent(self, consent_id: int, granted: bool, user_id: int) -> TelemedicineConsent:
        """Respond to consent request"""
        try:
            consent = self.db.query(TelemedicineConsent).filter(
                TelemedicineConsent.id == consent_id
            ).first()
            
            if not consent:
                raise ValueError("Consent request not found")
            
            consent.status = TelemedicineConsentStatus.GRANTED if granted else TelemedicineConsentStatus.DENIED
            consent.responded_at = datetime.utcnow()
            consent.responded_by = user_id
            
            # Update session based on consent type
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.id == consent.session_id
            ).first()
            
            if consent.consent_type == "recording":
                session.recording_consent_given = granted
            elif consent.consent_type == "screen_sharing":
                session.screen_sharing_consent_given = granted
            
            self.db.commit()
            self.db.refresh(consent)
            
            return TelemedicineConsent.from_orm(consent)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error responding to consent: {e}")
            raise

    # Analytics and Reporting
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a session"""
        try:
            session = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.session_id == session_id
            ).first()
            
            if not session:
                return {"error": "Session not found"}
            
            # Get session data
            messages_count = self.db.query(TelemedicineMessage).filter(
                TelemedicineMessage.session_id == session.id
            ).count()
            
            files_count = self.db.query(TelemedicineFile).filter(
                TelemedicineFile.session_id == session.id
            ).count()
            
            consents_count = self.db.query(TelemedicineConsent).filter(
                TelemedicineConsent.session_id == session.id
            ).count()
            
            return {
                "session_id": session_id,
                "duration_minutes": session.recording_duration / 60 if session.recording_duration else 0,
                "messages_count": messages_count,
                "files_shared": files_count,
                "consents_requested": consents_count,
                "recording_enabled": session.recording_enabled,
                "screen_sharing_enabled": session.screen_sharing_enabled,
                "chat_enabled": session.chat_enabled,
                "status": session.status.value,
                "participants": len(self.active_sessions.get(session_id, {}).get("participants", {}))
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {"error": str(e)}

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        return [
            {
                "session_id": session_id,
                "participants": list(info["participants"].keys()),
                "status": info["session"].status.value,
                "messages_count": len(info["messages"]),
                "files_count": len(info["files"]),
                "recording": info["recording"],
                "screen_sharing": info["screen_sharing"]
            }
            for session_id, info in self.active_sessions.items()
        ]

    # Configuration Management
    def get_configuration(self) -> TelemedicineConfiguration:
        """Get telemedicine configuration"""
        config = self.db.query(TelemedicineConfiguration).first()
        if not config:
            # Create default configuration
            config = TelemedicineConfiguration(
                max_sessions_per_doctor=10,
                session_duration_limit=120,  # 2 hours
                recording_enabled=True,
                screen_sharing_enabled=True,
                chat_enabled=True,
                patient_link_expiry_hours=24,
                webrtc_config={
                    "iceServers": self.signaling_servers,
                    "iceCandidatePoolSize": 10
                }
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        
        return TelemedicineConfiguration.from_orm(config)

    def update_configuration(self, config_data: TelemedicineConfigurationUpdate) -> TelemedicineConfiguration:
        """Update telemedicine configuration"""
        config = self.db.query(TelemedicineConfiguration).first()
        if not config:
            config = TelemedicineConfiguration(**config_data.dict())
            self.db.add(config)
        else:
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
        
        self.db.commit()
        self.db.refresh(config)
        return TelemedicineConfiguration.from_orm(config)
