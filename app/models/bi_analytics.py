from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.models.base import Base

class MetricType(enum.Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    PATIENT_SATISFACTION = "patient_satisfaction"
    STAFF_PERFORMANCE = "staff_performance"

class MetricPeriod(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class MetricStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class ClinicalMetric(Base):
    """Clinical performance metrics and KPIs"""
    __tablename__ = "clinical_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(200), nullable=False)
    metric_type = Column(Enum(MetricType), nullable=False)
    description = Column(Text)
    
    # Metric configuration
    target_value = Column(Float, nullable=True)
    threshold_warning = Column(Float, nullable=True)
    threshold_critical = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)  # percentage, count, days, etc.
    calculation_method = Column(String(100), nullable=False)  # SQL query or formula
    
    # Data source configuration
    data_source = Column(String(100), nullable=False)  # table or view name
    filters = Column(JSON, nullable=True)  # Additional filters for data extraction
    
    # Status and metadata
    status = Column(Enum(MetricStatus), default=MetricStatus.ACTIVE)
    is_system_metric = Column(Boolean, default=False)
    requires_permission = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    metric_values = relationship("MetricValue", back_populates="metric")
    alerts = relationship("MetricAlert", back_populates="metric")

class MetricValue(Base):
    """Historical values for clinical metrics"""
    __tablename__ = "metric_values"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("clinical_metrics.id"), nullable=False)
    
    # Value details
    value = Column(Float, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(Enum(MetricPeriod), nullable=False)
    
    # Additional context
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    data_points_count = Column(Integer, nullable=True)  # Number of data points used
    confidence_score = Column(Float, nullable=True)  # Confidence in the calculation
    
    # Relationships
    metric = relationship("ClinicalMetric", back_populates="metric_values")
    department = relationship("Department")
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient")

class MetricAlert(Base):
    """Alerts for metric threshold breaches"""
    __tablename__ = "metric_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("clinical_metrics.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # warning, critical, info
    threshold_breached = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    metric = relationship("ClinicalMetric", back_populates="alerts")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    creator = relationship("User", foreign_keys=[created_by])

class Dashboard(Base):
    """Customizable BI dashboards"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Dashboard configuration
    layout_config = Column(JSON, nullable=False)  # Dashboard layout and widget configuration
    filters_config = Column(JSON, nullable=True)  # Default filters and parameters
    refresh_interval = Column(Integer, default=300)  # Refresh interval in seconds
    
    # Access control
    is_public = Column(Boolean, default=False)
    is_system_dashboard = Column(Boolean, default=False)
    requires_permission = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    widgets = relationship("DashboardWidget", back_populates="dashboard")

class DashboardWidget(Base):
    """Widgets within dashboards"""
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=False)
    
    # Widget details
    widget_type = Column(String(50), nullable=False)  # chart, table, metric, kpi
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Widget configuration
    config = Column(JSON, nullable=False)  # Widget-specific configuration
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)
    height = Column(Integer, default=3)
    
    # Data source
    metric_id = Column(Integer, ForeignKey("clinical_metrics.id"), nullable=True)
    data_query = Column(Text, nullable=True)  # Custom SQL query for data
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")
    metric = relationship("ClinicalMetric")

class BIReport(Base):
    """Automated BI reports"""
    __tablename__ = "bi_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Report configuration
    report_type = Column(String(50), nullable=False)  # executive, operational, clinical, financial
    template_config = Column(JSON, nullable=False)  # Report template and layout
    data_queries = Column(JSON, nullable=False)  # Queries for data extraction
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    schedule_time = Column(String(10), nullable=True)  # HH:MM format
    last_generated = Column(DateTime(timezone=True), nullable=True)
    next_generation = Column(DateTime(timezone=True), nullable=True)
    
    # Recipients
    email_recipients = Column(JSON, nullable=True)  # List of email addresses
    notification_enabled = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    generations = relationship("BIReportGeneration", back_populates="report")

class BIReportGeneration(Base):
    """Generated BI reports"""
    __tablename__ = "bi_report_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("bi_reports.id"), nullable=False)
    
    # Generation details
    generation_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")  # pending, generating, completed, failed
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Data summary
    data_period_start = Column(DateTime(timezone=True), nullable=True)
    data_period_end = Column(DateTime(timezone=True), nullable=True)
    metrics_included = Column(JSON, nullable=True)  # List of metrics included
    
    # Processing information
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    report = relationship("BIReport", back_populates="generations")
    creator = relationship("User", foreign_keys=[created_by])

class PerformanceBenchmark(Base):
    """Performance benchmarks and targets"""
    __tablename__ = "performance_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    benchmark_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Benchmark configuration
    metric_type = Column(Enum(MetricType), nullable=False)
    specialty = Column(String(100), nullable=True)  # Medical specialty
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Target values
    target_value = Column(Float, nullable=False)
    minimum_acceptable = Column(Float, nullable=True)
    excellent_threshold = Column(Float, nullable=True)
    
    # Comparison data
    industry_average = Column(Float, nullable=True)
    peer_comparison = Column(JSON, nullable=True)  # Comparison with similar institutions
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    department = relationship("Department")
    creator = relationship("User", foreign_keys=[created_by])

class AnalyticsInsight(Base):
    """AI-generated insights and recommendations"""
    __tablename__ = "analytics_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String(50), nullable=False)  # trend, anomaly, recommendation, prediction
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Insight details
    confidence_score = Column(Float, nullable=False)  # 0-1 confidence in the insight
    impact_level = Column(String(20), nullable=False)  # low, medium, high, critical
    category = Column(String(50), nullable=False)  # clinical, financial, operational, quality
    
    # Related data
    related_metrics = Column(JSON, nullable=True)  # List of related metric IDs
    data_period_start = Column(DateTime(timezone=True), nullable=True)
    data_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # AI processing
    ai_model_version = Column(String(50), nullable=True)
    processing_parameters = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active, reviewed, dismissed, implemented
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    action_taken = Column(Text, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])

class DataQualityCheck(Base):
    """Data quality monitoring and validation"""
    __tablename__ = "data_quality_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Check configuration
    check_type = Column(String(50), nullable=False)  # completeness, accuracy, consistency, timeliness
    data_source = Column(String(100), nullable=False)
    validation_rules = Column(JSON, nullable=False)
    
    # Results
    last_check_date = Column(DateTime(timezone=True), nullable=True)
    quality_score = Column(Float, nullable=True)  # 0-1 quality score
    issues_found = Column(Integer, default=0)
    issues_resolved = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_fix_enabled = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    check_results = relationship("DataQualityResult", back_populates="check")

class DataQualityResult(Base):
    """Results of data quality checks"""
    __tablename__ = "data_quality_results"
    
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("data_quality_checks.id"), nullable=False)
    
    # Result details
    check_date = Column(DateTime(timezone=True), nullable=False)
    quality_score = Column(Float, nullable=False)
    total_records_checked = Column(Integer, nullable=False)
    records_with_issues = Column(Integer, default=0)
    
    # Issue details
    issues_found = Column(JSON, nullable=True)  # Detailed list of issues
    severity_distribution = Column(JSON, nullable=True)  # Distribution by severity
    
    # Processing information
    processing_time_seconds = Column(Float, nullable=True)
    auto_fixes_applied = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    check = relationship("DataQualityCheck", back_populates="check_results")
