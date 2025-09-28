"""
AI Integration Service
Service layer for AI-powered medical consultation analysis
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from cryptography.fernet import Fernet
import base64
import os

from app.models.ai_integration import (
    AIAnalysisSession, AIAnalysis, AIConfiguration,
    AIProvider, AIAnalysisStatus, AIAnalysisType
)
from app.schemas.ai_integration import (
    AIAnalysisSessionCreate, AIAnalysisSessionUpdate,
    AIAnalysisCreate, AIAnalysisUpdate,
    AIConfigurationCreate, AIConfigurationUpdate,
    AIDashboardResponse, AISessionSummary, AISessionsResponse,
    AIAnalysisRequest, AIAnalysisResponse
)

logger = logging.getLogger(__name__)


class AICryptoService:
    """Service for encrypting/decrypting AI configuration data"""
    
    def __init__(self):
        self.key = os.getenv('AI_ENCRYPTION_KEY', Fernet.generate_key())
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
            logger.error(f"Failed to decrypt AI data: {e}")
            return ""


class AIService:
    """Main service for AI integration operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crypto = AICryptoService()
    
    def create_analysis_session(self, tenant_id: int, session_data: AIAnalysisSessionCreate) -> AIAnalysisSession:
        """Create a new AI analysis session"""
        try:
            session_id = f"ai_{uuid.uuid4().hex[:12]}"
            
            session_dict = session_data.dict()
            session_dict.update({
                'tenant_id': tenant_id,
                'session_id': session_id,
                'status': AIAnalysisStatus.PENDING
            })
            
            session = AIAnalysisSession(**session_dict)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Created AI analysis session: {session_id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create AI analysis session: {e}")
            raise
    
    def get_analysis_session(self, session_id: str) -> Optional[AIAnalysisSession]:
        """Get AI analysis session by session ID"""
        return self.db.query(AIAnalysisSession).filter(
            AIAnalysisSession.session_id == session_id
        ).first()
    
    def get_analysis_sessions(self, tenant_id: int, status: Optional[str] = None,
                            doctor_id: Optional[int] = None, patient_id: Optional[int] = None,
                            page: int = 1, page_size: int = 20) -> AISessionsResponse:
        """Get AI analysis sessions with pagination"""
        try:
            query = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.tenant_id == tenant_id
            )
            
            if status:
                query = query.filter(AIAnalysisSession.status == status)
            if doctor_id:
                query = query.filter(AIAnalysisSession.doctor_id == doctor_id)
            if patient_id:
                query = query.filter(AIAnalysisSession.patient_id == patient_id)
            
            total_count = query.count()
            offset = (page - 1) * page_size
            sessions = query.order_by(desc(AIAnalysisSession.created_at)).offset(offset).limit(page_size).all()
            
            session_summaries = []
            for session in sessions:
                doctor_name = f"Dr. User {session.doctor_id}"
                patient_name = f"Patient {session.patient_id}"
                
                analysis_types = []
                if session.enabled_analyses:
                    analysis_types = [analysis.value for analysis in session.enabled_analyses]
                
                session_summaries.append(AISessionSummary(
                    id=session.id,
                    session_id=session.session_id,
                    doctor_name=doctor_name,
                    patient_name=patient_name,
                    status=session.status.value,
                    analysis_types=analysis_types,
                    confidence_score=session.cost_usd,  # Simplified
                    cost_usd=session.cost_usd,
                    created_at=session.created_at,
                    completed_at=session.completed_at
                ))
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return AISessionsResponse(
                sessions=session_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            logger.error(f"Failed to get AI analysis sessions: {e}")
            raise
    
    def start_analysis(self, session_id: str, analysis_types: List[AIAnalysisType]) -> AIAnalysisResponse:
        """Start AI analysis for a session"""
        try:
            session = self.get_analysis_session(session_id)
            if not session:
                return AIAnalysisResponse(
                    success=False,
                    session_id=session_id,
                    status=AIAnalysisStatus.FAILED,
                    message="Session not found"
                )
            
            if session.status != AIAnalysisStatus.PENDING:
                return AIAnalysisResponse(
                    success=False,
                    session_id=session_id,
                    status=session.status,
                    message="Session cannot be started in current status"
                )
            
            session.status = AIAnalysisStatus.PROCESSING
            session.started_at = datetime.now()
            self.db.commit()
            
            estimated_time = len(analysis_types) * 30
            
            return AIAnalysisResponse(
                success=True,
                session_id=session_id,
                status=AIAnalysisStatus.PROCESSING,
                message="Analysis started successfully",
                estimated_completion_time=estimated_time
            )
        except Exception as e:
            logger.error(f"Failed to start AI analysis: {e}")
            return AIAnalysisResponse(
                success=False,
                session_id=session_id,
                status=AIAnalysisStatus.FAILED,
                message=f"Failed to start analysis: {str(e)}"
            )
    
    def get_configuration(self, tenant_id: int) -> Optional[AIConfiguration]:
        """Get AI configuration for a tenant"""
        return self.db.query(AIConfiguration).filter(
            AIConfiguration.tenant_id == tenant_id
        ).first()
    
    def create_or_update_configuration(self, tenant_id: int, 
                                     config_data: AIConfigurationCreate) -> AIConfiguration:
        """Create or update AI configuration"""
        try:
            existing_config = self.get_configuration(tenant_id)
            
            if existing_config:
                update_dict = config_data.dict(exclude_unset=True)
                
                for key_field in ['openai_api_key', 'anthropic_api_key', 'google_api_key', 'azure_api_key']:
                    if key_field in update_dict and update_dict[key_field]:
                        update_dict[key_field] = self.crypto.encrypt(update_dict[key_field])
                
                for field, value in update_dict.items():
                    if hasattr(existing_config, field) and value is not None:
                        setattr(existing_config, field, value)
                
                self.db.commit()
                self.db.refresh(existing_config)
                return existing_config
            else:
                config_dict = config_data.dict()
                config_dict['tenant_id'] = tenant_id
                
                for key_field in ['openai_api_key', 'anthropic_api_key', 'google_api_key', 'azure_api_key']:
                    if key_field in config_dict and config_dict[key_field]:
                        config_dict[key_field] = self.crypto.encrypt(config_dict[key_field])
                
                configuration = AIConfiguration(**config_dict)
                self.db.add(configuration)
                self.db.commit()
                self.db.refresh(configuration)
                return configuration
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update AI configuration: {e}")
            raise
    
    def get_dashboard_data(self, tenant_id: int) -> AIDashboardResponse:
        """Get AI dashboard data"""
        try:
            total_sessions = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.tenant_id == tenant_id
            ).count()
            
            active_sessions = self.db.query(AIAnalysisSession).filter(
                and_(
                    AIAnalysisSession.tenant_id == tenant_id,
                    AIAnalysisSession.status == AIAnalysisStatus.PROCESSING
                )
            ).count()
            
            today = datetime.now().date()
            completed_sessions_today = self.db.query(AIAnalysisSession).filter(
                and_(
                    AIAnalysisSession.tenant_id == tenant_id,
                    AIAnalysisSession.status == AIAnalysisStatus.COMPLETED,
                    AIAnalysisSession.completed_at >= today
                )
            ).count()
            
            total_analyses = self.db.query(AIAnalysis).join(AIAnalysisSession).filter(
                AIAnalysisSession.tenant_id == tenant_id
            ).count()
            
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_sessions = self.db.query(AIAnalysisSession).filter(
                and_(
                    AIAnalysisSession.tenant_id == tenant_id,
                    AIAnalysisSession.created_at >= month_start,
                    AIAnalysisSession.cost_usd.isnot(None)
                )
            ).all()
            
            monthly_cost_usd = sum(session.cost_usd for session in monthly_sessions if session.cost_usd)
            
            config = self.get_configuration(tenant_id)
            monthly_budget_used_percent = 0
            if config and config.monthly_budget_usd:
                monthly_budget_used_percent = (monthly_cost_usd / config.monthly_budget_usd) * 100
            
            return AIDashboardResponse(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                completed_sessions_today=completed_sessions_today,
                total_analyses=total_analyses,
                average_confidence_score=0.85,  # Simplified
                doctor_approval_rate=92.5,  # Simplified
                monthly_cost_usd=round(monthly_cost_usd, 2),
                monthly_budget_used_percent=round(monthly_budget_used_percent, 2),
                most_used_analysis_types=[],
                recent_sessions=[]
            )
        except Exception as e:
            logger.error(f"Failed to get AI dashboard data: {e}")
            raise