"""
Security API Endpoints for Prontivus
Provides security monitoring, 2FA management, and audit endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.database.database import get_db
from app.services.security_monitor import get_security_monitor, SecurityMonitor
from app.services.audit_service import AuditService
from app.services.jwt_service import jwt_service, two_factor_service
from app.services.encryption_service import encryption_service
from app.core.exceptions import AuthenticationError
from app.schemas.auth import TwoFactorSetup

router = APIRouter()

# Pydantic models for security endpoints
class SecurityDashboardResponse(BaseModel):
    threat_statistics: Dict[str, int]
    recent_logins: Dict[str, int]
    top_threat_sources: List[Dict[str, Any]]
    recent_security_events: List[Dict[str, Any]]
    monitoring_status: Dict[str, int]
    generated_at: str

class TwoFactorSetupRequest(BaseModel):
    user_email: str

class TwoFactorVerifyRequest(BaseModel):
    secret: str
    code: str

class TwoFactorVerifyResponse(BaseModel):
    verified: bool
    message: str

class SecurityEventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    description: str
    detected_at: str
    action_taken: Optional[str]
    resolved: bool

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[str]
    user_id: Optional[int]
    success: bool
    risk_level: str
    created_at: str
    ip_address: Optional[str]

class EncryptionTestRequest(BaseModel):
    data: str

class EncryptionTestResponse(BaseModel):
    encrypted: str
    decrypted: str
    success: bool

@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    tenant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get security dashboard data"""
    try:
        security_monitor = get_security_monitor(db)
        dashboard_data = security_monitor.get_security_dashboard(tenant_id)
        
        return SecurityDashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security dashboard: {str(e)}"
        )

@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get security events with filtering"""
    try:
        audit_service = AuditService(db)
        events = audit_service.get_security_events(
            severity=severity,
            event_type=event_type,
            resolved=resolved,
            limit=limit,
            offset=offset
        )
        
        return [
            SecurityEventResponse(
                id=event.id,
                event_type=event.event_type,
                severity=event.severity,
                description=event.description,
                detected_at=event.detected_at.isoformat(),
                action_taken=event.action_taken,
                resolved=event.resolved
            ) for event in events
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security events: {str(e)}"
        )

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering"""
    try:
        audit_service = AuditService(db)
        logs = audit_service.get_audit_logs(
            user_id=user_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return [
            AuditLogResponse(
                id=log.id,
                action=log.action.value if hasattr(log.action, 'value') else str(log.action),
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                user_id=log.user_id,
                success=log.success,
                risk_level=log.risk_level,
                created_at=log.created_at.isoformat(),
                ip_address=log.ip_address
            ) for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )

@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_two_factor_auth(
    request_data: TwoFactorSetupRequest,
    db: Session = Depends(get_db)
):
    """Setup two-factor authentication for user"""
    try:
        setup_data = two_factor_service.setup_2fa(request_data.user_email)
        return setup_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}"
        )

@router.post("/2fa/verify", response_model=TwoFactorVerifyResponse)
async def verify_two_factor_setup(
    request_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify two-factor authentication setup"""
    try:
        verified = two_factor_service.verify_2fa_setup(
            request_data.secret,
            request_data.code
        )
        
        if verified:
            return TwoFactorVerifyResponse(
                verified=True,
                message="2FA setup verified successfully"
            )
        else:
            return TwoFactorVerifyResponse(
                verified=False,
                message="Invalid verification code"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}"
        )

@router.post("/encryption/test", response_model=EncryptionTestResponse)
async def test_encryption(
    request_data: EncryptionTestRequest,
    db: Session = Depends(get_db)
):
    """Test AES-256 encryption service"""
    try:
        # Encrypt data
        encrypted_data = encryption_service.encrypt_data(request_data.data)
        
        # Decrypt data
        decrypted_data = encryption_service.decrypt_data(encrypted_data)
        
        return EncryptionTestResponse(
            encrypted=encrypted_data,
            decrypted=str(decrypted_data),
            success=str(decrypted_data) == request_data.data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption test failed: {str(e)}"
        )

@router.get("/audit/report")
async def generate_audit_report(
    tenant_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Generate comprehensive audit report"""
    try:
        audit_service = AuditService(db)
        report = audit_service.generate_audit_report(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audit report: {str(e)}"
        )

@router.post("/monitoring/login-attempt")
async def monitor_login_attempt(
    email: str,
    success: bool,
    ip_address: str,
    user_agent: str,
    user_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Monitor login attempt for security threats"""
    try:
        security_monitor = get_security_monitor(db)
        threat_assessment = security_monitor.monitor_login_attempt(
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return threat_assessment
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login monitoring failed: {str(e)}"
        )

@router.post("/monitoring/data-access")
async def monitor_data_access(
    user_id: int,
    entity_type: str,
    entity_id: str,
    action: str,
    ip_address: str,
    tenant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Monitor data access for security threats"""
    try:
        security_monitor = get_security_monitor(db)
        threat_assessment = security_monitor.monitor_data_access(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            ip_address=ip_address,
            tenant_id=tenant_id
        )
        
        return threat_assessment
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data access monitoring failed: {str(e)}"
        )

@router.get("/jwt/info")
async def get_jwt_info():
    """Get JWT configuration information"""
    try:
        return {
            "algorithm": jwt_service.algorithm,
            "issuer": jwt_service.issuer,
            "audience": jwt_service.audience,
            "access_token_expire_minutes": jwt_service.access_token_expire_minutes,
            "refresh_token_expire_days": jwt_service.refresh_token_expire_days,
            "token_rotation_enabled": True,
            "version": "2.0"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get JWT info: {str(e)}"
        )

@router.post("/security/cleanup")
async def cleanup_security_data(db: Session = Depends(get_db)):
    """Clean up old security monitoring data"""
    try:
        security_monitor = get_security_monitor(db)
        security_monitor.cleanup_old_data()
        
        return {"message": "Security data cleanup completed"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security cleanup failed: {str(e)}"
        )

@router.get("/health")
async def security_health_check():
    """Security system health check"""
    try:
        # Check encryption service
        test_data = "health_check_test"
        encrypted = encryption_service.encrypt_data(test_data)
        decrypted = encryption_service.decrypt_data(encrypted)
        encryption_ok = str(decrypted) == test_data
        
        # Check JWT service
        jwt_ok = jwt_service.secret_key is not None
        
        # Check 2FA service
        totp_ok = two_factor_service.issuer is not None
        
        return {
            "status": "healthy",
            "services": {
                "encryption": "ok" if encryption_ok else "error",
                "jwt": "ok" if jwt_ok else "error",
                "2fa": "ok" if totp_ok else "error"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
