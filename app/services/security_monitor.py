"""
Security Monitoring Service for Prontivus
Implements real-time security monitoring, alerts, and threat detection
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict, deque
import ipaddress
import re
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from app.models.audit import SecurityEvent, AuditLog
from app.models.user import User
from app.services.audit_service import AuditService, EventType, SecurityLevel

logger = logging.getLogger(__name__)

class ThreatLevel(str, Enum):
    """Threat levels for security monitoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityRule(str, Enum):
    """Security rules for monitoring"""
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_LOGIN = "suspicious_login"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    UNUSUAL_LOCATION = "unusual_location"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ACCOUNT_TAKEOVER = "account_takeover"
    MALICIOUS_IP = "malicious_ip"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

class SecurityMonitor:
    """Real-time security monitoring service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        
        # In-memory tracking for real-time monitoring
        self.login_attempts = defaultdict(list)  # IP -> [timestamps]
        self.user_login_attempts = defaultdict(list)  # user_id -> [timestamps]
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.user_sessions = defaultdict(list)  # user_id -> [session_data]
        
        # Configuration
        self.max_login_attempts_per_hour = 10
        self.max_login_attempts_per_day = 50
        self.suspicious_threshold = 5
        self.block_threshold = 20
        
    def monitor_login_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Monitor login attempt and detect threats
        
        Args:
            email: User email
            success: Whether login was successful
            ip_address: Client IP address
            user_agent: Client user agent
            user_id: User ID if known
            tenant_id: Tenant ID
            
        Returns:
            Monitoring result with threat assessment
        """
        current_time = datetime.now(timezone.utc)
        threat_assessment = {
            "threat_level": ThreatLevel.LOW,
            "threats_detected": [],
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Track login attempts by IP
            self.login_attempts[ip_address].append(current_time)
            
            # Clean old attempts (older than 24 hours)
            cutoff_time = current_time - timedelta(hours=24)
            self.login_attempts[ip_address] = [
                attempt for attempt in self.login_attempts[ip_address]
                if attempt > cutoff_time
            ]
            
            # Track user login attempts
            if user_id:
                self.user_login_attempts[user_id].append(current_time)
                cutoff_time = current_time - timedelta(hours=24)
                self.user_login_attempts[user_id] = [
                    attempt for attempt in self.user_login_attempts[user_id]
                    if attempt > cutoff_time
                ]
            
            # Check for brute force attacks
            if not success:
                threat_assessment = self._check_brute_force(
                    email, ip_address, user_id, tenant_id, threat_assessment
                )
            
            # Check for suspicious patterns
            threat_assessment = self._check_suspicious_patterns(
                email, ip_address, user_agent, user_id, tenant_id, threat_assessment
            )
            
            # Check for account takeover attempts
            if user_id:
                threat_assessment = self._check_account_takeover(
                    user_id, ip_address, user_agent, tenant_id, threat_assessment
                )
            
            # Update threat level based on detected threats
            if threat_assessment["threats_detected"]:
                max_threat_level = max(
                    [self._get_threat_level(threat) for threat in threat_assessment["threats_detected"]],
                    default=ThreatLevel.LOW
                )
                threat_assessment["threat_level"] = max_threat_level
            
            # Log security event if threats detected
            if threat_assessment["threat_level"] != ThreatLevel.LOW:
                self.audit_service.log_security_event(
                    event_type=EventType.SUSPICIOUS_ACTIVITY,
                    severity=SecurityLevel(threat_assessment["threat_level"]),
                    description=f"Security threats detected during login: {', '.join(threat_assessment['threats_detected'])}",
                    user_id=user_id,
                    tenant_id=tenant_id,
                    source_ip=ip_address,
                    user_email=email,
                    details={
                        "threat_assessment": threat_assessment,
                        "login_success": success,
                        "user_agent": user_agent
                    },
                    action_taken="monitored"
                )
            
            return threat_assessment
            
        except Exception as e:
            logger.error(f"Login monitoring failed: {str(e)}")
            return threat_assessment
    
    def monitor_data_access(
        self,
        user_id: int,
        entity_type: str,
        entity_id: str,
        action: str,
        ip_address: str,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Monitor data access patterns
        
        Args:
            user_id: User ID
            entity_type: Type of data accessed
            entity_id: ID of data accessed
            action: Action performed
            ip_address: Client IP address
            tenant_id: Tenant ID
            
        Returns:
            Monitoring result
        """
        threat_assessment = {
            "threat_level": ThreatLevel.LOW,
            "threats_detected": [],
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Check for data exfiltration patterns
            threat_assessment = self._check_data_exfiltration(
                user_id, entity_type, action, ip_address, tenant_id, threat_assessment
            )
            
            # Check for privilege escalation
            threat_assessment = self._check_privilege_escalation(
                user_id, entity_type, action, tenant_id, threat_assessment
            )
            
            # Log data access
            self.audit_service.log_data_access(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                ip_address=ip_address,
                tenant_id=tenant_id,
                details={"monitoring_result": threat_assessment}
            )
            
            return threat_assessment
            
        except Exception as e:
            logger.error(f"Data access monitoring failed: {str(e)}")
            return threat_assessment
    
    def _check_brute_force(
        self,
        email: str,
        ip_address: str,
        user_id: Optional[int],
        tenant_id: Optional[int],
        threat_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for brute force attacks"""
        current_time = datetime.now(timezone.utc)
        
        # Check IP-based brute force
        recent_attempts = [
            attempt for attempt in self.login_attempts[ip_address]
            if attempt > current_time - timedelta(hours=1)
        ]
        
        if len(recent_attempts) >= self.max_login_attempts_per_hour:
            threat_assessment["threats_detected"].append(SecurityRule.BRUTE_FORCE)
            threat_assessment["actions_taken"].append("ip_monitored")
            threat_assessment["recommendations"].append("Consider IP blocking")
            
            # Log brute force event
            self.audit_service.detect_brute_force(
                email=email,
                ip_address=ip_address,
                attempt_count=len(recent_attempts),
                tenant_id=tenant_id
            )
        
        # Check user-based brute force
        if user_id:
            user_recent_attempts = [
                attempt for attempt in self.user_login_attempts[user_id]
                if attempt > current_time - timedelta(hours=1)
            ]
            
            if len(user_recent_attempts) >= self.suspicious_threshold:
                threat_assessment["threats_detected"].append(SecurityRule.MULTIPLE_FAILED_ATTEMPTS)
                threat_assessment["actions_taken"].append("account_monitored")
                threat_assessment["recommendations"].append("Consider account lockout")
        
        return threat_assessment
    
    def _check_suspicious_patterns(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        user_id: Optional[int],
        tenant_id: Optional[int],
        threat_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for suspicious patterns"""
        
        # Check for suspicious IP
        if self._is_suspicious_ip(ip_address):
            threat_assessment["threats_detected"].append(SecurityRule.MALICIOUS_IP)
            threat_assessment["actions_taken"].append("ip_flagged")
        
        # Check for suspicious user agent
        if self._is_suspicious_user_agent(user_agent):
            threat_assessment["threats_detected"].append(SecurityRule.SUSPICIOUS_LOGIN)
            threat_assessment["actions_taken"].append("user_agent_flagged")
        
        # Check for unusual login patterns
        if user_id and self._is_unusual_login_pattern(user_id, ip_address):
            threat_assessment["threats_detected"].append(SecurityRule.UNUSUAL_LOCATION)
            threat_assessment["actions_taken"].append("location_monitored")
        
        return threat_assessment
    
    def _check_account_takeover(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        tenant_id: Optional[int],
        threat_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for account takeover attempts"""
        
        # Check for rapid session changes
        if self._has_rapid_session_changes(user_id):
            threat_assessment["threats_detected"].append(SecurityRule.ACCOUNT_TAKEOVER)
            threat_assessment["actions_taken"].append("session_monitored")
            threat_assessment["recommendations"].append("Force re-authentication")
        
        # Check for unusual access patterns
        if self._has_unusual_access_pattern(user_id, ip_address):
            threat_assessment["threats_detected"].append(SecurityRule.ANOMALOUS_BEHAVIOR)
            threat_assessment["actions_taken"].append("behavior_monitored")
        
        return threat_assessment
    
    def _check_data_exfiltration(
        self,
        user_id: int,
        entity_type: str,
        action: str,
        ip_address: str,
        tenant_id: Optional[int],
        threat_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for data exfiltration patterns"""
        
        # Check for bulk data access
        if self._is_bulk_data_access(user_id, entity_type):
            threat_assessment["threats_detected"].append(SecurityRule.DATA_EXFILTRATION)
            threat_assessment["actions_taken"].append("bulk_access_monitored")
            threat_assessment["recommendations"].append("Review data access patterns")
        
        return threat_assessment
    
    def _check_privilege_escalation(
        self,
        user_id: int,
        entity_type: str,
        action: str,
        tenant_id: Optional[int],
        threat_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for privilege escalation attempts"""
        
        # Check for unauthorized access attempts
        if self._is_unauthorized_access(user_id, entity_type, action):
            threat_assessment["threats_detected"].append(SecurityRule.PRIVILEGE_ESCALATION)
            threat_assessment["actions_taken"].append("access_denied")
            threat_assessment["recommendations"].append("Review user permissions")
        
        return threat_assessment
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check if IP is in private range (might be suspicious for external access)
            if ip.is_private:
                return False
            
            # Check against known malicious IP ranges (simplified)
            # In production, you would use threat intelligence feeds
            suspicious_patterns = [
                r"^10\.0\.0\.",  # Example pattern
                r"^192\.168\.1\.",  # Example pattern
            ]
            
            for pattern in suspicious_patterns:
                if re.match(pattern, ip_address):
                    return True
            
            return False
            
        except ValueError:
            return True  # Invalid IP addresses are suspicious
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        if not user_agent:
            return True
        
        suspicious_patterns = [
            r"bot", r"crawler", r"spider", r"scraper",
            r"curl", r"wget", r"python", r"java",
            r"automated", r"script"
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True
        
        return False
    
    def _is_unusual_login_pattern(self, user_id: int, ip_address: str) -> bool:
        """Check for unusual login patterns"""
        # This would typically involve machine learning or statistical analysis
        # For now, we'll use a simple heuristic
        
        # Check if user has logged in from this IP before
        # In production, you would query historical login data
        return False
    
    def _has_rapid_session_changes(self, user_id: int) -> bool:
        """Check for rapid session changes"""
        current_time = datetime.now(timezone.utc)
        
        # Check if user has multiple recent sessions
        recent_sessions = [
            session for session in self.user_sessions[user_id]
            if session["timestamp"] > current_time - timedelta(minutes=30)
        ]
        
        return len(recent_sessions) > 3
    
    def _has_unusual_access_pattern(self, user_id: int, ip_address: str) -> bool:
        """Check for unusual access patterns"""
        # This would involve analyzing historical access patterns
        # For now, return False
        return False
    
    def _is_bulk_data_access(self, user_id: int, entity_type: str) -> bool:
        """Check for bulk data access patterns"""
        # This would involve analyzing data access patterns
        # For now, return False
        return False
    
    def _is_unauthorized_access(self, user_id: int, entity_type: str, action: str) -> bool:
        """Check for unauthorized access attempts"""
        # This would involve checking user permissions
        # For now, return False
        return False
    
    def _get_threat_level(self, threat: SecurityRule) -> ThreatLevel:
        """Get threat level for a security rule"""
        threat_levels = {
            SecurityRule.BRUTE_FORCE: ThreatLevel.HIGH,
            SecurityRule.SUSPICIOUS_LOGIN: ThreatLevel.MEDIUM,
            SecurityRule.MULTIPLE_FAILED_ATTEMPTS: ThreatLevel.MEDIUM,
            SecurityRule.UNUSUAL_LOCATION: ThreatLevel.MEDIUM,
            SecurityRule.PRIVILEGE_ESCALATION: ThreatLevel.HIGH,
            SecurityRule.DATA_EXFILTRATION: ThreatLevel.CRITICAL,
            SecurityRule.UNAUTHORIZED_ACCESS: ThreatLevel.HIGH,
            SecurityRule.ACCOUNT_TAKEOVER: ThreatLevel.CRITICAL,
            SecurityRule.MALICIOUS_IP: ThreatLevel.HIGH,
            SecurityRule.ANOMALOUS_BEHAVIOR: ThreatLevel.MEDIUM
        }
        
        return threat_levels.get(threat, ThreatLevel.LOW)
    
    def get_security_dashboard(self, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """Get security dashboard data"""
        try:
            current_time = datetime.now(timezone.utc)
            last_24h = current_time - timedelta(hours=24)
            last_7d = current_time - timedelta(days=7)
            
            # Get security events
            security_events = self.audit_service.get_security_events(
                resolved=False,
                limit=50
            )
            
            # Get threat statistics
            threat_stats = {
                "total_threats": len(security_events),
                "critical_threats": len([e for e in security_events if e.severity == "critical"]),
                "high_threats": len([e for e in security_events if e.severity == "high"]),
                "medium_threats": len([e for e in security_events if e.severity == "medium"]),
                "low_threats": len([e for e in security_events if e.severity == "low"])
            }
            
            # Get recent login attempts
            recent_logins = self.db.execute(text("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful,
                       SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed
                FROM audit_logs
                WHERE action IN ('login_success', 'login_failure')
                AND created_at >= :last_24h
                AND (:tenant_id IS NULL OR tenant_id = :tenant_id)
            """), {
                "last_24h": last_24h,
                "tenant_id": tenant_id
            }).fetchone()
            
            # Get top threat sources
            top_threat_sources = self.db.execute(text("""
                SELECT source_ip, COUNT(*) as count
                FROM security_events
                WHERE detected_at >= :last_7d
                AND (:tenant_id IS NULL OR tenant_id = :tenant_id)
                GROUP BY source_ip
                ORDER BY count DESC
                LIMIT 10
            """), {
                "last_7d": last_7d,
                "tenant_id": tenant_id
            }).fetchall()
            
            return {
                "threat_statistics": threat_stats,
                "recent_logins": {
                    "total": recent_logins[0] or 0,
                    "successful": recent_logins[1] or 0,
                    "failed": recent_logins[2] or 0
                },
                "top_threat_sources": [
                    {"ip": row[0], "count": row[1]} for row in top_threat_sources
                ],
                "recent_security_events": [
                    {
                        "id": event.id,
                        "type": event.event_type,
                        "severity": event.severity,
                        "description": event.description,
                        "detected_at": event.detected_at.isoformat(),
                        "action_taken": event.action_taken
                    } for event in security_events[:10]
                ],
                "monitoring_status": {
                    "active_monitors": len(self.login_attempts),
                    "blocked_ips": len(self.blocked_ips),
                    "suspicious_ips": len(self.suspicious_ips)
                },
                "generated_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Security dashboard generation failed: {str(e)}")
            return {"error": "Failed to generate security dashboard"}
    
    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(days=7)
            
            # Clean up old login attempts
            for ip in list(self.login_attempts.keys()):
                self.login_attempts[ip] = [
                    attempt for attempt in self.login_attempts[ip]
                    if attempt > cutoff_time
                ]
                if not self.login_attempts[ip]:
                    del self.login_attempts[ip]
            
            # Clean up old user attempts
            for user_id in list(self.user_login_attempts.keys()):
                self.user_login_attempts[user_id] = [
                    attempt for attempt in self.user_login_attempts[user_id]
                    if attempt > cutoff_time
                ]
                if not self.user_login_attempts[user_id]:
                    del self.user_login_attempts[user_id]
            
            logger.info("Security monitoring data cleanup completed")
            
        except Exception as e:
            logger.error(f"Security monitoring cleanup failed: {str(e)}")

# Global security monitor instance
security_monitor = None

def get_security_monitor(db: Session) -> SecurityMonitor:
    """Get security monitor instance"""
    global security_monitor
    if security_monitor is None:
        security_monitor = SecurityMonitor(db)
    return security_monitor
