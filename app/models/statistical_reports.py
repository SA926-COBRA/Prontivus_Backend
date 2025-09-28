from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.models.base import Base

class ReportType(enum.Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"

class ReportFormat(enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"

class ReportStatus(enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReportFrequency(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class StatisticalReport(Base):
    """Statistical reports with various metrics and analytics"""
    __tablename__ = "statistical_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report Configuration
    report_format = Column(Enum(ReportFormat), default=ReportFormat.PDF)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=True)
    parameters = Column(JSON, nullable=True)  # Report parameters and filters
    
    # Data Configuration
    data_source = Column(String(100), nullable=False)  # Table or view name
    query_filters = Column(JSON, nullable=True)  # SQL filters
    date_range_start = Column(Date, nullable=True)
    date_range_end = Column(Date, nullable=True)
    
    # Generation Settings
    frequency = Column(Enum(ReportFrequency), default=ReportFrequency.ONCE)
    scheduled_time = Column(String(10), nullable=True)  # HH:MM format
    auto_generate = Column(Boolean, default=False)
    
    # Status and Tracking
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    last_generated = Column(DateTime(timezone=True), nullable=True)
    next_generation = Column(DateTime(timezone=True), nullable=True)
    generation_count = Column(Integer, default=0)
    
    # File Information
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    template = relationship("ReportTemplate", back_populates="reports")
    generations = relationship("ReportGeneration", back_populates="report")

class ReportTemplate(Base):
    """Report templates for consistent formatting"""
    __tablename__ = "statistical_report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(Enum(ReportType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template Configuration
    template_content = Column(Text, nullable=False)  # HTML/Jinja2 template
    css_styles = Column(Text, nullable=True)
    header_template = Column(Text, nullable=True)
    footer_template = Column(Text, nullable=True)
    
    # Layout Settings
    page_size = Column(String(20), default="A4")  # A4, Letter, etc.
    orientation = Column(String(10), default="portrait")  # portrait, landscape
    margins = Column(JSON, nullable=True)  # top, bottom, left, right
    
    # Default Settings
    default_parameters = Column(JSON, nullable=True)
    default_filters = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System templates cannot be deleted
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    reports = relationship("StatisticalReport", back_populates="template")

class ReportGeneration(Base):
    """Report generation logs and history"""
    __tablename__ = "report_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("statistical_reports.id"), nullable=False)
    
    # Generation Details
    generation_start = Column(DateTime(timezone=True), nullable=False)
    generation_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.GENERATING)
    
    # Parameters Used
    parameters_used = Column(JSON, nullable=True)
    filters_applied = Column(JSON, nullable=True)
    date_range_used = Column(JSON, nullable=True)
    
    # Results
    records_processed = Column(Integer, default=0)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Performance Metrics
    generation_time_seconds = Column(Float, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    report = relationship("StatisticalReport", back_populates="generations")
    generator = relationship("User", foreign_keys=[generated_by])

class ReportMetric(Base):
    """Metrics and KPIs for reports"""
    __tablename__ = "report_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(200), nullable=False)
    metric_type = Column(String(50), nullable=False)  # count, sum, average, percentage, etc.
    description = Column(Text, nullable=True)
    
    # Metric Configuration
    data_source = Column(String(100), nullable=False)
    calculation_query = Column(Text, nullable=True)  # SQL for calculation
    calculation_formula = Column(Text, nullable=True)  # Mathematical formula
    unit = Column(String(50), nullable=True)  # %, $, count, etc.
    
    # Display Settings
    display_format = Column(String(50), nullable=True)  # Number format
    decimal_places = Column(Integer, default=2)
    show_trend = Column(Boolean, default=True)
    show_comparison = Column(Boolean, default=True)
    
    # Thresholds and Alerts
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    alert_enabled = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    values = relationship("ReportMetricValue", back_populates="metric")

class ReportMetricValue(Base):
    """Metric values for specific time periods"""
    __tablename__ = "report_metric_values"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("report_metrics.id"), nullable=False)
    
    # Value Details
    value = Column(Numeric(15, 4), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, etc.
    
    # Additional Data
    raw_data = Column(JSON, nullable=True)  # Raw data used for calculation
    report_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Comparison Data
    previous_value = Column(Numeric(15, 4), nullable=True)
    change_percentage = Column(Float, nullable=True)
    trend_direction = Column(String(10), nullable=True)  # up, down, stable
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    metric = relationship("ReportMetric", back_populates="values")

class ReportDashboard(Base):
    """Dashboard configurations for reports"""
    __tablename__ = "report_dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Dashboard Configuration
    layout_config = Column(JSON, nullable=False)  # Dashboard layout
    widgets = Column(JSON, nullable=False)  # Widget configurations
    filters = Column(JSON, nullable=True)  # Global filters
    
    # Display Settings
    refresh_interval = Column(Integer, default=300)  # seconds
    auto_refresh = Column(Boolean, default=True)
    show_filters = Column(Boolean, default=True)
    
    # Access Control
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, nullable=True)  # Roles that can access
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class ReportAccessLog(Base):
    """Access logs for reports and dashboards"""
    __tablename__ = "statistical_report_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Access Details
    report_id = Column(Integer, ForeignKey("statistical_reports.id"), nullable=True)
    dashboard_id = Column(Integer, ForeignKey("report_dashboards.id"), nullable=True)
    access_type = Column(String(50), nullable=False)  # view, download, generate
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Access Details
    access_time = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Additional Data
    parameters_used = Column(JSON, nullable=True)
    filters_applied = Column(JSON, nullable=True)
    
    # Relationships
    report = relationship("StatisticalReport")
    dashboard = relationship("ReportDashboard")
    user = relationship("User")

class ReportSchedule(Base):
    """Scheduled report generation"""
    __tablename__ = "statistical_report_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("statistical_reports.id"), nullable=False)
    
    # Schedule Configuration
    frequency = Column(Enum(ReportFrequency), nullable=False)
    scheduled_time = Column(String(10), nullable=True)  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Schedule Details
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Notification Settings
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_emails = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    report = relationship("StatisticalReport")
    creator = relationship("User", foreign_keys=[created_by])
