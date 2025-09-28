"""
Telemedicine Service
Service layer for native telemedicine video platform
"""

import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from cryptography.fernet import Fernet
import base64
import os

from app.models.telemedicine import (
    TelemedicineSession, TelemedicineMessage, TelemedicineFile, 
    TelemedicineConsent, TelemedicineConfiguration, TelemedicineAnalytics,
    TelemedicineSessionStatus, TelemedicineConsentStatus
)
from app.schemas.telemedicine import (
    TelemedicineSessionCreate, TelemedicineSessionUpdate,
    TelemedicineMessageCreate, TelemedicineFileCreate,
    TelemedicineConsentCreate, TelemedicineConsentUpdate,
    TelemedicineConfigurationCreate, TelemedicineConfigurationUpdate,
    TelemedicineAnalyticsCreate, TelemedicineDashboardResponse,
    TelemedicineSessionSummary, TelemedicineSessionsResponse
)

logger = logging.getLogger(__name__)


class TelemedicineCryptoService:
    """Service for encrypting/decrypting telemedicine data"""
    
    def __init__(self):
        # In production, this should come from environment variables
        self.key = os.getenv('TELEMEDICINE_ENCRYPTION_KEY', Fernet.generate_key())
        if isinstance(self.key, str):
            self.key = self.key.encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt telemedicine data: {e}")
            return ""


class TelemedicineService:
    """Main service for telemedicine operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crypto = TelemedicineCryptoService()
    
    # Session Management
    def create_session(self, tenant_id: int, session_data: TelemedicineSessionCreate) -> TelemedicineSession:
        """Create a new telemedicine session"""
        try:
            # Generate unique session ID
            session_id = f"tm_{uuid.uuid4().hex[:12]}"
            
            # Create room URL (in production, this would integrate with video platform)
            room_url = f"https://telemedicine.prontivus.com/room/{session_id}"
            
            # Generate room token (encrypted)
            room_token = self.crypto.encrypt(f"{session_id}:{tenant_id}")
            
            session_dict = session_data.dict()
            session_dict.update({
                'tenant_id': tenant_id,
                'session_id': session_id,
                'room_url': room_url,
                'room_token': room_token,
                'max_participants': 2,
                'status': TelemedicineSessionStatus.SCHEDULED,
                'consent_granted': False
            })
            
            session = TelemedicineSession(**session_dict)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Created telemedicine session: {session_id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create telemedicine session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[TelemedicineSession]:
        """Get telemedicine session by session ID"""
        return self.db.query(TelemedicineSession).filter(
            TelemedicineSession.session_id == session_id
        ).first()
    
    def get_session_by_id(self, session_id: int) -> Optional[TelemedicineSession]:
        """Get telemedicine session by ID"""
        return self.db.query(TelemedicineSession).filter(
            TelemedicineSession.id == session_id
        ).first()
    
    def get_sessions(self, tenant_id: int, status: Optional[str] = None, 
                    doctor_id: Optional[int] = None, patient_id: Optional[int] = None,
                    page: int = 1, page_size: int = 20) -> TelemedicineSessionsResponse:
        """Get telemedicine sessions with pagination"""
        try:
            query = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.tenant_id == tenant_id
            )
            
            if status:
                query = query.filter(TelemedicineSession.status == status)
            if doctor_id:
                query = query.filter(TelemedicineSession.doctor_id == doctor_id)
            if patient_id:
                query = query.filter(TelemedicineSession.patient_id == patient_id)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            sessions = query.order_by(desc(TelemedicineSession.scheduled_start)).offset(offset).limit(page_size).all()
            
            # Convert to summary format
            session_summaries = []
            for session in sessions:
                # Get doctor and patient names (simplified - in production, join with user/patient tables)
                doctor_name = f"Dr. User {session.doctor_id}"  # Replace with actual join
                patient_name = f"Patient {session.patient_id}"  # Replace with actual join
                
                duration_minutes = None
                if session.actual_start and session.actual_end:
                    duration = session.actual_end - session.actual_start
                    duration_minutes = int(duration.total_seconds() / 60)
                
                session_summaries.append(TelemedicineSessionSummary(
                    id=session.id,
                    session_id=session.session_id,
                    title=session.title,
                    doctor_name=doctor_name,
                    patient_name=patient_name,
                    status=session.status.value,
                    scheduled_start=session.scheduled_start,
                    actual_start=session.actual_start,
                    actual_end=session.actual_end,
                    duration_minutes=duration_minutes,
                    connection_quality=session.connection_quality,
                    recording_enabled=session.recording_enabled,
                    consent_granted=session.consent_granted
                ))
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return TelemedicineSessionsResponse(
                sessions=session_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            logger.error(f"Failed to get telemedicine sessions: {e}")
            raise
    
    def update_session(self, session_id: int, update_data: TelemedicineSessionUpdate) -> Optional[TelemedicineSession]:
        """Update telemedicine session"""
        try:
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(session, field) and value is not None:
                    setattr(session, field, value)
            
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Updated telemedicine session: {session.session_id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update telemedicine session: {e}")
            raise
    
    def start_session(self, session_id: str) -> Optional[TelemedicineSession]:
        """Start a telemedicine session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return None
            
            if session.status != TelemedicineSessionStatus.SCHEDULED:
                raise ValueError("Session cannot be started in current status")
            
            session.status = TelemedicineSessionStatus.IN_PROGRESS
            session.actual_start = datetime.now()
            
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Started telemedicine session: {session_id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start telemedicine session: {e}")
            raise
    
    def end_session(self, session_id: str, reason: Optional[str] = None) -> Optional[TelemedicineSession]:
        """End a telemedicine session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return None
            
            if session.status not in [TelemedicineSessionStatus.IN_PROGRESS, TelemedicineSessionStatus.WAITING]:
                raise ValueError("Session cannot be ended in current status")
            
            session.status = TelemedicineSessionStatus.COMPLETED
            session.actual_end = datetime.now()
            
            # Update metadata with end reason
            if not session.metadata:
                session.metadata = {}
            session.metadata['end_reason'] = reason
            session.metadata['end_timestamp'] = datetime.now().isoformat()
            
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Ended telemedicine session: {session_id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to end telemedicine session: {e}")
            raise
    
    def join_session(self, session_id: str, participant_type: str, participant_id: int) -> Dict[str, Any]:
        """Join a telemedicine session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"success": False, "message": "Session not found"}
            
            if session.status not in [TelemedicineSessionStatus.SCHEDULED, TelemedicineSessionStatus.WAITING]:
                return {"success": False, "message": "Session not available for joining"}
            
            # Check participant authorization
            if participant_type == "doctor" and session.doctor_id != participant_id:
                return {"success": False, "message": "Unauthorized doctor"}
            elif participant_type == "patient" and session.patient_id != participant_id:
                return {"success": False, "message": "Unauthorized patient"}
            
            # Check consent for patients
            if participant_type == "patient" and session.consent_required and not session.consent_granted:
                return {"success": False, "message": "Patient consent required"}
            
            # Update session status if needed
            if session.status == TelemedicineSessionStatus.SCHEDULED:
                session.status = TelemedicineSessionStatus.WAITING
            
            # Decrypt room token for participant
            decrypted_token = self.crypto.decrypt(session.room_token)
            
            self.db.commit()
            
            return {
                "success": True,
                "room_url": session.room_url,
                "room_token": decrypted_token,
                "session_status": session.status.value,
                "message": "Successfully joined session"
            }
        except Exception as e:
            logger.error(f"Failed to join telemedicine session: {e}")
            return {"success": False, "message": f"Join failed: {str(e)}"}
    
    # Consent Management
    def create_consent_request(self, session_id: str, consent_data: TelemedicineConsentCreate) -> TelemedicineConsent:
        """Create a consent request for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError("Session not found")
            
            consent_dict = consent_data.dict()
            consent_dict.update({
                'session_id': session.id,
                'patient_id': session.patient_id,
                'status': TelemedicineConsentStatus.PENDING
            })
            
            consent = TelemedicineConsent(**consent_dict)
            self.db.add(consent)
            self.db.commit()
            self.db.refresh(consent)
            
            logger.info(f"Created consent request for session: {session_id}")
            return consent
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create consent request: {e}")
            raise
    
    def grant_consent(self, consent_id: int, ip_address: Optional[str] = None, 
                     user_agent: Optional[str] = None) -> Optional[TelemedicineConsent]:
        """Grant consent for a telemedicine session"""
        try:
            consent = self.db.query(TelemedicineConsent).filter(
                TelemedicineConsent.id == consent_id
            ).first()
            
            if not consent:
                return None
            
            if consent.status != TelemedicineConsentStatus.PENDING:
                raise ValueError("Consent cannot be granted in current status")
            
            consent.status = TelemedicineConsentStatus.GRANTED
            consent.granted = True
            consent.granted_at = datetime.now()
            consent.ip_address = ip_address
            consent.user_agent = user_agent
            
            # Update session consent status
            session = self.get_session_by_id(consent.session_id)
            if session:
                session.consent_granted = True
                session.consent_granted_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(consent)
            logger.info(f"Granted consent: {consent_id}")
            return consent
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to grant consent: {e}")
            raise
    
    # Message Management
    def send_message(self, session_id: str, message_data: TelemedicineMessageCreate, 
                    sender_id: int, sender_type: str) -> TelemedicineMessage:
        """Send a message in a telemedicine session"""
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError("Session not found")
            
            message_dict = message_data.dict()
            message_dict.update({
                'session_id': session.id,
                'sender_id': sender_id,
                'sender_type': sender_type,
                'is_encrypted': True
            })
            
            # Encrypt message content
            message_dict['content'] = self.crypto.encrypt(message_dict['content'])
            
            message = TelemedicineMessage(**message_dict)
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            logger.info(f"Sent message in session: {session_id}")
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to send message: {e}")
            raise
    
    def get_messages(self, session_id: str, limit: int = 50) -> List[TelemedicineMessage]:
        """Get messages for a telemedicine session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return []
            
            messages = self.db.query(TelemedicineMessage).filter(
                and_(
                    TelemedicineMessage.session_id == session.id,
                    TelemedicineMessage.is_deleted == False
                )
            ).order_by(TelemedicineMessage.created_at.desc()).limit(limit).all()
            
            # Decrypt message content
            for message in messages:
                message.content = self.crypto.decrypt(message.content)
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    # Configuration Management
    def get_configuration(self, tenant_id: int) -> Optional[TelemedicineConfiguration]:
        """Get telemedicine configuration for a tenant"""
        return self.db.query(TelemedicineConfiguration).filter(
            TelemedicineConfiguration.tenant_id == tenant_id
        ).first()
    
    def create_or_update_configuration(self, tenant_id: int, 
                                     config_data: TelemedicineConfigurationCreate) -> TelemedicineConfiguration:
        """Create or update telemedicine configuration"""
        try:
            existing_config = self.get_configuration(tenant_id)
            
            if existing_config:
                # Update existing configuration
                update_dict = config_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    if hasattr(existing_config, field) and value is not None:
                        setattr(existing_config, field, value)
                self.db.commit()
                self.db.refresh(existing_config)
                return existing_config
            else:
                # Create new configuration
                config_dict = config_data.dict()
                config_dict['tenant_id'] = tenant_id
                configuration = TelemedicineConfiguration(**config_dict)
                self.db.add(configuration)
                self.db.commit()
                self.db.refresh(configuration)
                return configuration
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update telemedicine configuration: {e}")
            raise
    
    # Analytics and Dashboard
    def get_dashboard_data(self, tenant_id: int) -> TelemedicineDashboardResponse:
        """Get telemedicine dashboard data"""
        try:
            # Get counts
            total_sessions = self.db.query(TelemedicineSession).filter(
                TelemedicineSession.tenant_id == tenant_id
            ).count()
            
            active_sessions = self.db.query(TelemedicineSession).filter(
                and_(
                    TelemedicineSession.tenant_id == tenant_id,
                    TelemedicineSession.status.in_([
                        TelemedicineSessionStatus.IN_PROGRESS,
                        TelemedicineSessionStatus.WAITING
                    ])
                )
            ).count()
            
            # Sessions completed today
            today = datetime.now().date()
            completed_sessions_today = self.db.query(TelemedicineSession).filter(
                and_(
                    TelemedicineSession.tenant_id == tenant_id,
                    TelemedicineSession.status == TelemedicineSessionStatus.COMPLETED,
                    TelemedicineSession.actual_end >= today
                )
            ).count()
            
            # Average session duration
            completed_sessions = self.db.query(TelemedicineSession).filter(
                and_(
                    TelemedicineSession.tenant_id == tenant_id,
                    TelemedicineSession.status == TelemedicineSessionStatus.COMPLETED,
                    TelemedicineSession.actual_start.isnot(None),
                    TelemedicineSession.actual_end.isnot(None)
                )
            ).all()
            
            total_duration = 0
            session_count = 0
            for session in completed_sessions:
                if session.actual_start and session.actual_end:
                    duration = session.actual_end - session.actual_start
                    total_duration += duration.total_seconds() / 60  # Convert to minutes
                    session_count += 1
            
            average_session_duration = total_duration / session_count if session_count > 0 else 0
            
            # Patient satisfaction average
            analytics = self.db.query(TelemedicineAnalytics).filter(
                and_(
                    TelemedicineAnalytics.tenant_id == tenant_id,
                    TelemedicineAnalytics.patient_satisfaction_rating.isnot(None)
                )
            ).all()
            
            satisfaction_sum = sum(a.patient_satisfaction_rating for a in analytics if a.patient_satisfaction_rating)
            satisfaction_count = len([a for a in analytics if a.patient_satisfaction_rating])
            patient_satisfaction_average = satisfaction_sum / satisfaction_count if satisfaction_count > 0 else 0
            
            # Technical issues today
            technical_issues_today = self.db.query(TelemedicineSession).filter(
                and_(
                    TelemedicineSession.tenant_id == tenant_id,
                    TelemedicineSession.created_at >= today,
                    TelemedicineSession.technical_issues.isnot(None)
                )
            ).count()
            
            # Upcoming sessions
            upcoming_sessions = self.db.query(TelemedicineSession).filter(
                and_(
                    TelemedicineSession.tenant_id == tenant_id,
                    TelemedicineSession.status == TelemedicineSessionStatus.SCHEDULED,
                    TelemedicineSession.scheduled_start > datetime.now()
                )
            ).count()
            
            # Recording storage (simplified calculation)
            recording_storage_used_mb = 0  # In production, calculate actual storage usage
            
            return TelemedicineDashboardResponse(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                completed_sessions_today=completed_sessions_today,
                average_session_duration=round(average_session_duration, 2),
                patient_satisfaction_average=round(patient_satisfaction_average, 2),
                technical_issues_today=technical_issues_today,
                upcoming_sessions=upcoming_sessions,
                recording_storage_used_mb=recording_storage_used_mb
            )
        except Exception as e:
            logger.error(f"Failed to get telemedicine dashboard data: {e}")
            raise
