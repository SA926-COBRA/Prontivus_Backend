from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

# Enums
class MetricType(str, Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    PATIENT_SATISFACTION = "patient_satisfaction"
    STAFF_PERFORMANCE = "staff_performance"

class MetricPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class MetricStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# Clinical Metric schemas
class ClinicalMetricBase(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=200)
    metric_type: MetricType
    description: Optional[str] = None
    target_value: Optional[float] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    calculation_method: str = Field(..., max_length=100)
    data_source: str = Field(..., max_length=100)
    filters: Optional[Dict[str, Any]] = None
    is_system_metric: bool = False
    requires_permission: bool = False

class ClinicalMetricCreate(ClinicalMetricBase):
    pass

class ClinicalMetricUpdate(BaseModel):
    metric_name: Optional[str] = Field(None, min_length=1, max_length=200)
    metric_type: Optional[MetricType] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    calculation_method: Optional[str] = Field(None, max_length=100)
    data_source: Optional[str] = Field(None, max_length=100)
    filters: Optional[Dict[str, Any]] = None
    status: Optional[MetricStatus] = None
    requires_permission: Optional[bool] = None

class ClinicalMetric(ClinicalMetricBase):
    id: int
    status: MetricStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Metric Value schemas
class MetricValueBase(BaseModel):
    metric_id: int
    value: float
    period_start: datetime
    period_end: datetime
    period_type: MetricPeriod
    department_id: Optional[int] = None
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    data_points_count: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class MetricValueCreate(MetricValueBase):
    pass

class MetricValueUpdate(BaseModel):
    value: Optional[float] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    period_type: Optional[MetricPeriod] = None
    department_id: Optional[int] = None
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    data_points_count: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class MetricValue(MetricValueBase):
    id: int
    calculated_at: datetime

    class Config:
        from_attributes = True

# Metric Alert schemas
class MetricAlertBase(BaseModel):
    metric_id: int
    alert_type: str = Field(..., pattern="^(warning|critical|info)$")
    threshold_breached: float
    current_value: float
    message: str

class MetricAlertCreate(MetricAlertBase):
    pass

class MetricAlertUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(active|acknowledged|resolved)$")
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None

class MetricAlert(MetricAlertBase):
    id: int
    status: str
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    triggered_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Dashboard schemas
class DashboardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Dict[str, Any]
    filters_config: Optional[Dict[str, Any]] = None
    refresh_interval: int = Field(300, ge=60, le=3600)
    is_public: bool = False
    is_system_dashboard: bool = False
    requires_permission: bool = False

class DashboardCreate(DashboardBase):
    pass

class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    filters_config: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = Field(None, ge=60, le=3600)
    is_public: Optional[bool] = None
    requires_permission: Optional[bool] = None
    is_active: Optional[bool] = None

class Dashboard(DashboardBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Dashboard Widget schemas
class DashboardWidgetBase(BaseModel):
    dashboard_id: int
    widget_type: str = Field(..., pattern="^(chart|table|metric|kpi)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    config: Dict[str, Any]
    position_x: int = Field(0, ge=0)
    position_y: int = Field(0, ge=0)
    width: int = Field(4, ge=1, le=12)
    height: int = Field(3, ge=1, le=12)
    metric_id: Optional[int] = None
    data_query: Optional[str] = None

class DashboardWidgetCreate(DashboardWidgetBase):
    pass

class DashboardWidgetUpdate(BaseModel):
    widget_type: Optional[str] = Field(None, pattern="^(chart|table|metric|kpi)$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position_x: Optional[int] = Field(None, ge=0)
    position_y: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=1, le=12)
    height: Optional[int] = Field(None, ge=1, le=12)
    metric_id: Optional[int] = None
    data_query: Optional[str] = None
    is_active: Optional[bool] = None

class DashboardWidget(DashboardWidgetBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# BI Report schemas
class BIReportBase(BaseModel):
    report_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: str = Field(..., pattern="^(executive|operational|clinical|financial)$")
    template_config: Dict[str, Any]
    data_queries: Dict[str, Any]
    is_scheduled: bool = False
    schedule_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    schedule_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    email_recipients: Optional[List[str]] = None
    notification_enabled: bool = True

class BIReportCreate(BIReportBase):
    pass

class BIReportUpdate(BaseModel):
    report_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[str] = Field(None, pattern="^(executive|operational|clinical|financial)$")
    template_config: Optional[Dict[str, Any]] = None
    data_queries: Optional[Dict[str, Any]] = None
    is_scheduled: Optional[bool] = None
    schedule_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    schedule_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    email_recipients: Optional[List[str]] = None
    notification_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class BIReport(BIReportBase):
    id: int
    last_generated: Optional[datetime] = None
    next_generation: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# BI Report Generation schemas
class BIReportGenerationBase(BaseModel):
    report_id: int
    generation_date: datetime
    data_period_start: Optional[datetime] = None
    data_period_end: Optional[datetime] = None
    metrics_included: Optional[List[int]] = None

class BIReportGenerationCreate(BIReportGenerationBase):
    pass

class BIReportGenerationUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|generating|completed|failed)$")
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

class BIReportGeneration(BIReportGenerationBase):
    id: int
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Performance Benchmark schemas
class PerformanceBenchmarkBase(BaseModel):
    benchmark_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    metric_type: MetricType
    specialty: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    target_value: float
    minimum_acceptable: Optional[float] = None
    excellent_threshold: Optional[float] = None
    industry_average: Optional[float] = None
    peer_comparison: Optional[Dict[str, Any]] = None
    effective_date: date
    expiry_date: Optional[date] = None

class PerformanceBenchmarkCreate(PerformanceBenchmarkBase):
    pass

class PerformanceBenchmarkUpdate(BaseModel):
    benchmark_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    metric_type: Optional[MetricType] = None
    specialty: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    target_value: Optional[float] = None
    minimum_acceptable: Optional[float] = None
    excellent_threshold: Optional[float] = None
    industry_average: Optional[float] = None
    peer_comparison: Optional[Dict[str, Any]] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: Optional[bool] = None

class PerformanceBenchmark(PerformanceBenchmarkBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Analytics Insight schemas
class AnalyticsInsightBase(BaseModel):
    insight_type: str = Field(..., pattern="^(trend|anomaly|recommendation|prediction)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    confidence_score: float = Field(..., ge=0, le=1)
    impact_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    category: str = Field(..., pattern="^(clinical|financial|operational|quality)$")
    related_metrics: Optional[List[int]] = None
    data_period_start: Optional[datetime] = None
    data_period_end: Optional[datetime] = None
    ai_model_version: Optional[str] = Field(None, max_length=50)
    processing_parameters: Optional[Dict[str, Any]] = None

class AnalyticsInsightCreate(AnalyticsInsightBase):
    pass

class AnalyticsInsightUpdate(BaseModel):
    insight_type: Optional[str] = Field(None, pattern="^(trend|anomaly|recommendation|prediction)$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    impact_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    category: Optional[str] = Field(None, pattern="^(clinical|financial|operational|quality)$")
    related_metrics: Optional[List[int]] = None
    data_period_start: Optional[datetime] = None
    data_period_end: Optional[datetime] = None
    ai_model_version: Optional[str] = Field(None, max_length=50)
    processing_parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(active|reviewed|dismissed|implemented)$")
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = None

class AnalyticsInsight(AnalyticsInsightBase):
    id: int
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    generated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Data Quality Check schemas
class DataQualityCheckBase(BaseModel):
    check_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    check_type: str = Field(..., pattern="^(completeness|accuracy|consistency|timeliness)$")
    data_source: str = Field(..., max_length=100)
    validation_rules: Dict[str, Any]
    auto_fix_enabled: bool = False

class DataQualityCheckCreate(DataQualityCheckBase):
    pass

class DataQualityCheckUpdate(BaseModel):
    check_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    check_type: Optional[str] = Field(None, pattern="^(completeness|accuracy|consistency|timeliness)$")
    data_source: Optional[str] = Field(None, max_length=100)
    validation_rules: Optional[Dict[str, Any]] = None
    auto_fix_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class DataQualityCheck(DataQualityCheckBase):
    id: int
    last_check_date: Optional[datetime] = None
    quality_score: Optional[float] = None
    issues_found: int
    issues_resolved: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Data Quality Result schemas
class DataQualityResultBase(BaseModel):
    check_id: int
    check_date: datetime
    quality_score: float = Field(..., ge=0, le=1)
    total_records_checked: int = Field(..., ge=0)
    records_with_issues: int = Field(0, ge=0)
    issues_found: Optional[Dict[str, Any]] = None
    severity_distribution: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = None
    auto_fixes_applied: int = Field(0, ge=0)

class DataQualityResultCreate(DataQualityResultBase):
    pass

class DataQualityResult(DataQualityResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard and Analytics Response schemas
class DashboardData(BaseModel):
    dashboard_id: int
    dashboard_name: str
    widgets: List[Dict[str, Any]]
    last_updated: datetime

class MetricTrend(BaseModel):
    metric_id: int
    metric_name: str
    values: List[Dict[str, Any]]
    trend_direction: str  # up, down, stable
    trend_percentage: float
    period: str

class PerformanceComparison(BaseModel):
    metric_id: int
    metric_name: str
    current_value: float
    target_value: float
    industry_average: Optional[float] = None
    peer_average: Optional[float] = None
    performance_score: float  # 0-100
    status: str  # excellent, good, needs_improvement, poor

class BIInsightsSummary(BaseModel):
    total_insights: int
    insights_by_type: Dict[str, int]
    insights_by_category: Dict[str, int]
    high_impact_insights: int
    unread_insights: int
    recent_insights: List[Dict[str, Any]]

class DataQualitySummary(BaseModel):
    overall_quality_score: float
    checks_performed: int
    issues_found: int
    issues_resolved: int
    quality_by_source: Dict[str, float]
    recent_checks: List[Dict[str, Any]]

# Request schemas
class MetricCalculationRequest(BaseModel):
    metric_id: int
    period_start: datetime
    period_end: datetime
    filters: Optional[Dict[str, Any]] = None

class DashboardDataRequest(BaseModel):
    dashboard_id: int
    filters: Optional[Dict[str, Any]] = None
    refresh_cache: bool = False

class BIReportGenerationRequest(BaseModel):
    report_id: int
    data_period_start: Optional[datetime] = None
    data_period_end: Optional[datetime] = None
    include_insights: bool = True
    format: str = Field("pdf", pattern="^(pdf|excel|html)$")

class AnalyticsInsightRequest(BaseModel):
    category: Optional[str] = None
    insight_type: Optional[str] = None
    confidence_threshold: float = Field(0.7, ge=0, le=1)
    impact_level: Optional[str] = None
    data_period_days: int = Field(30, ge=1, le=365)
