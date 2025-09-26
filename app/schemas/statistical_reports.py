from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class ReportType(str, Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"

class ReportStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReportFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# Statistical Report schemas
class StatisticalReportBase(BaseModel):
    report_name: str = Field(..., min_length=1, max_length=200)
    report_type: ReportType
    description: Optional[str] = None
    report_format: ReportFormat = ReportFormat.PDF
    template_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    data_source: str = Field(..., min_length=1, max_length=100)
    query_filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    frequency: ReportFrequency = ReportFrequency.ONCE
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    auto_generate: bool = False

class StatisticalReportCreate(StatisticalReportBase):
    pass

class StatisticalReportUpdate(BaseModel):
    report_name: Optional[str] = Field(None, min_length=1, max_length=200)
    report_type: Optional[ReportType] = None
    description: Optional[str] = None
    report_format: Optional[ReportFormat] = None
    template_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    data_source: Optional[str] = Field(None, min_length=1, max_length=100)
    query_filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    frequency: Optional[ReportFrequency] = None
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    auto_generate: Optional[bool] = None

class StatisticalReport(StatisticalReportBase):
    id: int
    status: ReportStatus
    last_generated: Optional[datetime] = None
    next_generation: Optional[datetime] = None
    generation_count: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Template schemas
class ReportTemplateBase(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=200)
    template_type: ReportType
    description: Optional[str] = None
    template_content: str
    css_styles: Optional[str] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    page_size: str = Field("A4", max_length=20)
    orientation: str = Field("portrait", regex="^(portrait|landscape)$")
    margins: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None

class ReportTemplateCreate(ReportTemplateBase):
    pass

class ReportTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, min_length=1, max_length=200)
    template_type: Optional[ReportType] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    css_styles: Optional[str] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    page_size: Optional[str] = Field(None, max_length=20)
    orientation: Optional[str] = Field(None, regex="^(portrait|landscape)$")
    margins: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ReportTemplate(ReportTemplateBase):
    id: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Generation schemas
class ReportGenerationBase(BaseModel):
    report_id: int
    generation_start: datetime
    generation_end: Optional[datetime] = None
    status: ReportStatus = ReportStatus.GENERATING
    parameters_used: Optional[Dict[str, Any]] = None
    filters_applied: Optional[Dict[str, Any]] = None
    date_range_used: Optional[Dict[str, Any]] = None
    records_processed: int = 0
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    generation_time_seconds: Optional[float] = None
    memory_used_mb: Optional[float] = None

class ReportGenerationCreate(ReportGenerationBase):
    pass

class ReportGenerationUpdate(BaseModel):
    generation_end: Optional[datetime] = None
    status: Optional[ReportStatus] = None
    parameters_used: Optional[Dict[str, Any]] = None
    filters_applied: Optional[Dict[str, Any]] = None
    date_range_used: Optional[Dict[str, Any]] = None
    records_processed: Optional[int] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    generation_time_seconds: Optional[float] = None
    memory_used_mb: Optional[float] = None

class ReportGeneration(ReportGenerationBase):
    id: int
    created_at: datetime
    generated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Metric schemas
class ReportMetricBase(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=200)
    metric_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    data_source: str = Field(..., min_length=1, max_length=100)
    calculation_query: Optional[str] = None
    calculation_formula: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    display_format: Optional[str] = Field(None, max_length=50)
    decimal_places: int = Field(2, ge=0, le=10)
    show_trend: bool = True
    show_comparison: bool = True
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    alert_enabled: bool = False

class ReportMetricCreate(ReportMetricBase):
    pass

class ReportMetricUpdate(BaseModel):
    metric_name: Optional[str] = Field(None, min_length=1, max_length=200)
    metric_type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    data_source: Optional[str] = Field(None, min_length=1, max_length=100)
    calculation_query: Optional[str] = None
    calculation_formula: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)
    display_format: Optional[str] = Field(None, max_length=50)
    decimal_places: Optional[int] = Field(None, ge=0, le=10)
    show_trend: Optional[bool] = None
    show_comparison: Optional[bool] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    alert_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class ReportMetric(ReportMetricBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Metric Value schemas
class ReportMetricValueBase(BaseModel):
    metric_id: int
    value: Decimal = Field(..., ge=0)
    period_start: datetime
    period_end: datetime
    period_type: str = Field(..., min_length=1, max_length=20)
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    previous_value: Optional[Decimal] = None
    change_percentage: Optional[float] = None
    trend_direction: Optional[str] = Field(None, regex="^(up|down|stable)$")

class ReportMetricValueCreate(ReportMetricValueBase):
    pass

class ReportMetricValueUpdate(BaseModel):
    value: Optional[Decimal] = Field(None, ge=0)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    period_type: Optional[str] = Field(None, min_length=1, max_length=20)
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    previous_value: Optional[Decimal] = None
    change_percentage: Optional[float] = None
    trend_direction: Optional[str] = Field(None, regex="^(up|down|stable)$")

class ReportMetricValue(ReportMetricValueBase):
    id: int
    calculated_at: datetime

    class Config:
        from_attributes = True

# Report Dashboard schemas
class ReportDashboardBase(BaseModel):
    dashboard_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Dict[str, Any]
    widgets: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    refresh_interval: int = Field(300, ge=60, le=3600)
    auto_refresh: bool = True
    show_filters: bool = True
    is_public: bool = False
    allowed_roles: Optional[List[str]] = None

class ReportDashboardCreate(ReportDashboardBase):
    pass

class ReportDashboardUpdate(BaseModel):
    dashboard_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    widgets: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = Field(None, ge=60, le=3600)
    auto_refresh: Optional[bool] = None
    show_filters: Optional[bool] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ReportDashboard(ReportDashboardBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Access Log schemas
class ReportAccessLogBase(BaseModel):
    report_id: Optional[int] = None
    dashboard_id: Optional[int] = None
    access_type: str = Field(..., min_length=1, max_length=50)
    user_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    duration_seconds: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    parameters_used: Optional[Dict[str, Any]] = None
    filters_applied: Optional[Dict[str, Any]] = None

class ReportAccessLogCreate(ReportAccessLogBase):
    pass

class ReportAccessLog(ReportAccessLogBase):
    id: int
    access_time: datetime

    class Config:
        from_attributes = True

# Report Schedule schemas
class ReportScheduleBase(BaseModel):
    report_id: int
    frequency: ReportFrequency
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field("UTC", max_length=50)
    start_date: date
    end_date: Optional[date] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool = True
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: Optional[List[str]] = None

class ReportScheduleCreate(ReportScheduleBase):
    pass

class ReportScheduleUpdate(BaseModel):
    frequency: Optional[ReportFrequency] = None
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: Optional[bool] = None
    run_count: Optional[int] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_emails: Optional[List[str]] = None

class ReportSchedule(ReportScheduleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Request/Response schemas
class ReportSearchRequest(BaseModel):
    report_name: Optional[str] = None
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    created_by: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class ReportGenerationRequest(BaseModel):
    report_id: int
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    format: Optional[ReportFormat] = None

class ReportSummary(BaseModel):
    total_reports: int
    active_reports: int
    reports_by_type: Dict[str, int]
    reports_by_status: Dict[str, int]
    total_generations: int
    successful_generations: int
    failed_generations: int
    total_downloads: int

class MetricCalculationRequest(BaseModel):
    metric_id: int
    period_start: datetime
    period_end: datetime
    period_type: str = "daily"
    include_trend: bool = True
    include_comparison: bool = True

class DashboardDataRequest(BaseModel):
    dashboard_id: int
    filters: Optional[Dict[str, Any]] = None
    refresh_data: bool = False

class ReportAnalytics(BaseModel):
    total_reports: int
    reports_generated_today: int
    reports_generated_this_week: int
    reports_generated_this_month: int
    most_accessed_reports: List[Dict[str, Any]]
    generation_success_rate: float
    average_generation_time: float
    top_report_types: List[Dict[str, Any]]
    user_activity: List[Dict[str, Any]]
