"""
Prontivus Configuration Settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Prontivus"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Branding
    BRAND_NAME: str = "Prontivus"
    BRAND_SLOGAN: str = "Cuidado inteligente"
    BRAND_LOGO_URL: str = "/Logo/Prontivus Horizontal.png"
    BRAND_COLOR_PRIMARY: str = "#2563eb"  # Blue
    BRAND_COLOR_SECONDARY: str = "#059669"  # Green
    BRAND_COLOR_ACCENT: str = "#dc2626"  # Red
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_ASYNC: Optional[str] = None
    SQLITE_URL: str = "sqlite:///./prontivus_offline.db"
    USE_SQLITE: bool = True
    
    # PostgreSQL Production Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "prontivus"
    POSTGRES_USER: str = "prontivus_user"
    POSTGRES_PASSWORD: str = "prontivus_password"
    POSTGRES_SSL_MODE: str = "prefer"  # prefer, require, disable
    
    # Connection Pool Settings - Optimized for Render
    DB_POOL_SIZE: int = 5  # Reduced for Render's limitations
    DB_MAX_OVERFLOW: int = 10  # Reduced overflow
    DB_POOL_TIMEOUT: int = 10  # Reduced timeout
    DB_POOL_RECYCLE: int = 1800  # 30 minutes instead of 1 hour
    DB_POOL_PRE_PING: bool = True
    
    # Sync Configuration
    SYNC_ENABLED: bool = True
    SYNC_INTERVAL_SECONDS: int = 300  # 5 minutes
    SYNC_BATCH_SIZE: int = 1000
    SYNC_CONFLICT_RESOLUTION: str = "postgresql_wins"  # postgresql_wins, sqlite_wins, manual
    SYNC_RETRY_ATTEMPTS: int = 3
    SYNC_RETRY_DELAY: int = 5
    
    # Offline Mode Settings
    OFFLINE_MODE_ENABLED: bool = True
    OFFLINE_DATA_RETENTION_DAYS: int = 30
    OFFLINE_SYNC_ON_STARTUP: bool = True
    OFFLINE_CONFLICT_NOTIFICATION: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "https://prontivus-frontend.vercel.app",
        "https://prontivus-frontend-git-main-prontivus.vercel.app", 
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Fallback for development
    ]
    ALLOWED_HOSTS: List[str] = [
        "prontivus-backend-pa1e.onrender.com",
        "prontivus-frontend.vercel.app",
        "localhost", 
        "127.0.0.1",
        "*"
    ]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Medical System
    TISS_VERSION: str = "3.05.00"
    DEFAULT_TIMEZONE: str = "America/Sao_Paulo"
    
    # Internationalization
    DEFAULT_LANGUAGE: str = "pt-BR"
    SUPPORTED_LANGUAGES: List[str] = ["pt-BR", "en-US", "es-ES"]
    LANGUAGE_FALLBACK: str = "pt-BR"
    
    # Licensing
    LICENSE_SIGNATURE_KEY: str = "license-signature-key"
    OFFLINE_GRACE_PERIOD_HOURS: int = 72
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    @property
    def constructed_database_url(self) -> str:
        """Construct DATABASE_URL from individual components if not provided directly"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Construct from individual PostgreSQL settings
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def constructed_database_url_async(self) -> str:
        """Construct DATABASE_URL_ASYNC from individual components if not provided directly"""
        if self.DATABASE_URL_ASYNC:
            return self.DATABASE_URL_ASYNC
        
        # Construct from individual PostgreSQL settings
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env file

# Create settings instance
settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
