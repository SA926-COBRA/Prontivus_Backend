"""
Enhanced Security Configuration for Prontivus
Implements JWT + 2FA, AES-256 encryption, TLS 1.3, audit logs & alerts
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
import secrets
import base64

class SecuritySettings(BaseSettings):
    """Enhanced security settings"""
    
    # JWT Security Enhancements
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"  # Can be upgraded to RS256 for production
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced for security
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "prontivus-medical-system"
    JWT_AUDIENCE: str = "prontivus-users"
    
    # Token Security
    JWT_TOKEN_ROTATION_ENABLED: bool = True
    JWT_REFRESH_TOKEN_ROTATION: bool = True
    JWT_MAX_REFRESH_ATTEMPTS: int = 3
    
    # 2FA Configuration
    TOTP_ISSUER: str = "Prontivus Medical"
    TOTP_WINDOW: int = 1  # Allow 1 window for clock drift
    TOTP_SECRET_LENGTH: int = 32
    BACKUP_CODES_COUNT: int = 10
    BACKUP_CODE_LENGTH: int = 8
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_HISTORY_COUNT: int = 5  # Prevent password reuse
    PASSWORD_EXPIRY_DAYS: int = 90
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 30
    INACTIVE_SESSION_TIMEOUT_MINUTES: int = 15
    
    # AES-256 Encryption
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    ENCRYPTED_FIELDS: List[str] = [
        "cpf", "phone", "address", "medical_records", 
        "prescriptions", "billing_info", "insurance_info"
    ]
    
    # TLS Configuration
    TLS_VERSION: str = "1.3"
    TLS_CIPHER_SUITES: List[str] = [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256"
    ]
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True
    
    # Security Headers
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years for compliance
    AUDIT_LOG_ENCRYPTION: bool = True
    AUDIT_LOG_COMPRESSION: bool = True
    
    # Security Monitoring
    SECURITY_MONITORING_ENABLED: bool = True
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 3
    BRUTE_FORCE_DETECTION_WINDOW_MINUTES: int = 15
    IP_WHITELIST_ENABLED: bool = False
    IP_BLACKLIST_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_LOGIN_ATTEMPTS_PER_HOUR: int = 10
    RATE_LIMIT_API_CALLS_PER_MINUTE: int = 100
    
    # Data Protection
    DATA_MASKING_ENABLED: bool = True
    PII_ENCRYPTION_ENABLED: bool = True
    DATA_RETENTION_POLICY_DAYS: int = 2555  # 7 years
    
    # Compliance
    LGPD_COMPLIANCE_ENABLED: bool = True
    HIPAA_COMPLIANCE_ENABLED: bool = True
    GDPR_COMPLIANCE_ENABLED: bool = True
    
    # Backup Security
    BACKUP_ENCRYPTION_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 90
    BACKUP_INTEGRITY_CHECK: bool = True
    
    # API Security
    API_VERSIONING_ENABLED: bool = True
    API_DEPRECATION_NOTICE_DAYS: int = 90
    API_RATE_LIMITING_ENABLED: bool = True
    
    # CORS Security
    CORS_ALLOWED_ORIGINS: List[str] = []
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOWED_HEADERS: List[str] = ["Authorization", "Content-Type"]
    CORS_MAX_AGE: int = 86400  # 24 hours
    
    @field_validator('CORS_ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Environment-specific settings
    ENVIRONMENT: str = "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    def get_encryption_key(self) -> bytes:
        """Get encryption key as bytes"""
        return base64.urlsafe_b64decode(self.ENCRYPTION_KEY.encode())
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        return self.JWT_SECRET_KEY
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# Create security settings instance
security_settings = SecuritySettings()
