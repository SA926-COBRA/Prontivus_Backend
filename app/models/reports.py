from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.database import Base

class ReportType(enum.Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    COMMERCIAL = "commercial"
    AUDIT = "audit"
    CUSTOM = "custom"

class ReportFormat(enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"

class ReportStatus(enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class ReportTemplate(Base):
    """Report templates for different types of reports"""
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False)
    template_data = Column(JSON)  # Template configuration and layout
    
    # Template settings
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)  # System vs user-created
    requires_permission = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    reports = relationship("GeneratedReport", back_populates="template")

class GeneratedReport(Base):
    """Generated reports tracking"""
    __tablename__ = "generated_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Report details
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    report_format = Column(Enum(ReportFormat), nullable=False)
    
    # Report parameters and filters
    parameters = Column(JSON)  # Report parameters and filters used
    date_range_start = Column(DateTime(timezone=True))
    date_range_end = Column(DateTime(timezone=True))
    
    # File information
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)  # Size in bytes
    download_count = Column(Integer, default=0)
    
    # Status and metadata
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    error_message = Column(Text)
    generated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    template = relationship("ReportTemplate", back_populates="reports")
    creator = relationship("User", foreign_keys=[created_by])

class ReportSchedule(Base):
    """Scheduled reports for automatic generation"""
    __tablename__ = "report_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Schedule details
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    schedule_config = Column(JSON)  # Cron-like configuration
    
    # Recipients
    email_recipients = Column(JSON)  # List of email addresses
    notification_enabled = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    template = relationship("ReportTemplate")
    creator = relationship("User", foreign_keys=[created_by])

class ReportAccessLog(Base):
    """Log of report access and downloads"""
    __tablename__ = "report_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("generated_reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Access details
    access_type = Column(String(20), nullable=False)  # view, download, print
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Metadata
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    report = relationship("GeneratedReport")
    user = relationship("User", foreign_keys=[user_id])
