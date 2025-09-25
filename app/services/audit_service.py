"""
Enhanced Audit Logging Service for Prontivus
Implements comprehensive audit logging with security monitoring
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import uuid

from app.models.audit import AuditLog, SecurityEvent, AuditAction
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)

class SecurityLevel(str, Enum):
    """Security levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventType(str, Enum):
    """Types of security events"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    PERMISSION_CHANGE = "permission_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

class AuditService:
    """Enhanced audit logging service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = encryption_service
    
    def log_event(
        self,
        action: Union[str, AuditAction],
        entity_type: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        risk_level: str = "low",
        risk_factors: Optional[List[str]] = None,
        lgpd_relevant: bool = False,
        hipaa_relevant: bool = False,
        requires_review: bool = False
    ) -> AuditLog:
        """
        Log an audit event
        
        Args:
            action: Action performed
            entity_type: Type of entity affected
            user_id: ID of user performing action
            tenant_id: Tenant ID
            entity_id: ID of affected entity
            details: Additional details
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session ID
            request_id: Request ID for tracing
            success: Whether action was successful
            error_message: Error message if failed
            risk_level: Risk level (low, medium, high, critical)
            risk_factors: Factors contributing to risk
            lgpd_relevant: Whether event is LGPD relevant
            hipaa_relevant: Whether event is HIPAA relevant
            requires_review: Whether event requires manual review
            
        Returns:
            Created AuditLog instance
        """
        try:
            # Convert string action to enum if needed
            if isinstance(action, str):
                try:
                    action = AuditAction(action)
                except ValueError:
                    # If action doesn't exist in enum, create a custom one
                    pass
            
            # Encrypt sensitive details if needed
            encrypted_details = None
            if details:
                encrypted_details = self._encrypt_sensitive_data(details)
            
            encrypted_old_values = None
            if old_values:
                encrypted_old_values = self._encrypt_sensitive_data(old_values)
            
            encrypted_new_values = None
            if new_values:
                encrypted_new_values = self._encrypt_sensitive_data(new_values)
            
            # Create audit log entry
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                request_id=request_id or str(uuid.uuid4()),
                details=encrypted_details,
                old_values=encrypted_old_values,
                new_values=encrypted_new_values,
                success=success,
                error_message=error_message,
                risk_level=risk_level,
                risk_factors=risk_factors,
                lgpd_relevant=lgpd_relevant,
                hipaa_relevant=hipaa_relevant,
                requires_review=requires_review,
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            # Log to application logger
            logger.info(f"Audit event logged: {action} on {entity_type} by user {user_id}")
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            self.db.rollback()
            raise
    
    def log_security_event(
        self,
        event_type: Union[str, EventType],
        severity: Union[str, SecurityLevel],
        description: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        source_ip: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        action_taken: Optional[str] = None
    ) -> SecurityEvent:
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            severity: Severity level
            description: Event description
            user_id: User ID if applicable
            tenant_id: Tenant ID
            source_ip: Source IP address
            user_email: User email if applicable
            details: Additional event details
            action_taken: Action taken in response
            
        Returns:
            Created SecurityEvent instance
        """
        try:
            # Convert string enums if needed
            if isinstance(event_type, str):
                try:
                    event_type = EventType(event_type)
                except ValueError:
                    pass
            
            if isinstance(severity, str):
                try:
                    severity = SecurityLevel(severity)
                except ValueError:
                    severity = SecurityLevel.MEDIUM
            
            # Encrypt sensitive details
            encrypted_details = None
            if details:
                encrypted_details = self._encrypt_sensitive_data(details)
            
            security_event = SecurityEvent(
                tenant_id=tenant_id,
                event_type=str(event_type),
                severity=str(severity),
                source_ip=source_ip,
                user_id=user_id,
                user_email=user_email,
                description=description,
                details=encrypted_details,
                action_taken=action_taken,
                detected_at=datetime.now(timezone.utc)
            )
            
            self.db.add(security_event)
            self.db.commit()
            self.db.refresh(security_event)
            
            # Log to application logger with appropriate level
            if severity == SecurityLevel.CRITICAL:
                logger.critical(f"CRITICAL security event: {event_type} - {description}")
            elif severity == SecurityLevel.HIGH:
                logger.error(f"HIGH security event: {event_type} - {description}")
            elif severity == SecurityLevel.MEDIUM:
                logger.warning(f"MEDIUM security event: {event_type} - {description}")
            else:
                logger.info(f"LOW security event: {event_type} - {description}")
            
            return security_event
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            self.db.rollback()
            raise
    
    def log_login_attempt(
        self,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        failure_reason: Optional[str] = None
    ):
        """Log login attempt"""
        action = AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE
        
        details = {
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success
        }
        
        if not success and failure_reason:
            details["failure_reason"] = failure_reason
        
        risk_level = "high" if not success else "low"
        risk_factors = ["authentication_failure"] if not success else None
        
        self.log_event(
            action=action,
            entity_type="user",
            user_id=user_id,
            tenant_id=tenant_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=failure_reason,
            risk_level=risk_level,
            risk_factors=risk_factors,
            lgpd_relevant=True,
            hipaa_relevant=True
        )
        
        # Log security event for failed attempts
        if not success:
            self.log_security_event(
                event_type=EventType.LOGIN_FAILURE,
                severity=SecurityLevel.MEDIUM,
                description=f"Failed login attempt for {email}",
                user_id=user_id,
                tenant_id=tenant_id,
                source_ip=ip_address,
                user_email=email,
                details=details,
                action_taken="logged"
            )
    
    def log_data_access(
        self,
        user_id: int,
        entity_type: str,
        entity_id: str,
        action: str,
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data access event"""
        self.log_event(
            action=AuditAction.DATA_ACCESS,
            entity_type=entity_type,
            user_id=user_id,
            tenant_id=tenant_id,
            entity_id=entity_id,
            details={
                "access_type": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **(details or {})
            },
            ip_address=ip_address,
            lgpd_relevant=True,
            hipaa_relevant=True
        )
    
    def log_data_modification(
        self,
        user_id: int,
        entity_type: str,
        entity_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """Log data modification event"""
        self.log_event(
            action=AuditAction.DATA_MODIFICATION,
            entity_type=entity_type,
            user_id=user_id,
            tenant_id=tenant_id,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            lgpd_relevant=True,
            hipaa_relevant=True,
            requires_review=True
        )
    
    def detect_suspicious_activity(
        self,
        user_id: Optional[int],
        activity_type: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """Detect and log suspicious activity"""
        self.log_security_event(
            event_type=EventType.SUSPICIOUS_ACTIVITY,
            severity=SecurityLevel.HIGH,
            description=f"Suspicious activity detected: {activity_type}",
            user_id=user_id,
            tenant_id=tenant_id,
            source_ip=ip_address,
            details=details,
            action_taken="investigation_required"
        )
    
    def detect_brute_force(
        self,
        email: str,
        ip_address: str,
        attempt_count: int,
        tenant_id: Optional[int] = None
    ):
        """Detect and log brute force attack"""
        self.log_security_event(
            event_type=EventType.BRUTE_FORCE_ATTEMPT,
            severity=SecurityLevel.CRITICAL,
            description=f"Brute force attack detected for {email}",
            tenant_id=tenant_id,
            source_ip=ip_address,
            user_email=email,
            details={
                "attempt_count": attempt_count,
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            action_taken="account_locked"
        )
    
    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data in audit details"""
        if not data:
            return data
        
        # Fields that should be encrypted
        sensitive_fields = [
            'password', 'cpf', 'rg', 'phone', 'email', 'address',
            'medical_record', 'prescription', 'billing_info'
        ]
        
        encrypted_data = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields and isinstance(value, str):
                # Mask sensitive data instead of encrypting for audit logs
                if key.lower() == 'password':
                    encrypted_data[key] = "***MASKED***"
                elif key.lower() in ['cpf', 'rg']:
                    encrypted_data[key] = f"{value[:3]}***{value[-2:]}" if len(value) > 5 else "***MASKED***"
                elif key.lower() == 'email':
                    parts = value.split('@')
                    if len(parts) == 2:
                        encrypted_data[key] = f"{parts[0][:2]}***@{parts[1]}"
                    else:
                        encrypted_data[key] = "***MASKED***"
                else:
                    encrypted_data[key] = "***MASKED***"
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Retrieve audit logs with filtering"""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_security_events(
        self,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SecurityEvent]:
        """Retrieve security events with filtering"""
        query = self.db.query(SecurityEvent)
        
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        if resolved is not None:
            query = query.filter(SecurityEvent.resolved == resolved)
        
        return query.order_by(SecurityEvent.detected_at.desc()).offset(offset).limit(limit).all()
    
    def generate_audit_report(
        self,
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            # Base query
            query = self.db.query(AuditLog)
            if tenant_id:
                query = query.filter(AuditLog.tenant_id == tenant_id)
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # Get statistics
            total_events = query.count()
            successful_events = query.filter(AuditLog.success == True).count()
            failed_events = query.filter(AuditLog.success == False).count()
            
            # Risk level distribution
            risk_levels = {}
            for level in ['low', 'medium', 'high', 'critical']:
                risk_levels[level] = query.filter(AuditLog.risk_level == level).count()
            
            # Top actions
            top_actions = self.db.execute(text("""
                SELECT action, COUNT(*) as count
                FROM audit_logs
                WHERE (:tenant_id IS NULL OR tenant_id = :tenant_id)
                AND (:start_date IS NULL OR created_at >= :start_date)
                AND (:end_date IS NULL OR created_at <= :end_date)
                GROUP BY action
                ORDER BY count DESC
                LIMIT 10
            """), {
                "tenant_id": tenant_id,
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()
            
            # Top users
            top_users = self.db.execute(text("""
                SELECT user_id, COUNT(*) as count
                FROM audit_logs
                WHERE user_id IS NOT NULL
                AND (:tenant_id IS NULL OR tenant_id = :tenant_id)
                AND (:start_date IS NULL OR created_at >= :start_date)
                AND (:end_date IS NULL OR created_at <= :end_date)
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """), {
                "tenant_id": tenant_id,
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()
            
            return {
                "summary": {
                    "total_events": total_events,
                    "successful_events": successful_events,
                    "failed_events": failed_events,
                    "success_rate": (successful_events / total_events * 100) if total_events > 0 else 0
                },
                "risk_distribution": risk_levels,
                "top_actions": [{"action": row[0], "count": row[1]} for row in top_actions],
                "top_users": [{"user_id": row[0], "count": row[1]} for row in top_users],
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise
