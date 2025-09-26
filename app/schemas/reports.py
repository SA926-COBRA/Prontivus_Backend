from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class ReportType(str, Enum):
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    COMMERCIAL = "commercial"
    AUDIT = "audit"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"

class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

# Report Template schemas
class ReportTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: ReportType
    template_data: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_system_template: bool = False
    requires_permission: bool = False

class ReportTemplateCreate(ReportTemplateBase):
    pass

class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[ReportType] = None
    template_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    requires_permission: Optional[bool] = None

class ReportTemplate(ReportTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Generated Report schemas
class ReportParameters(BaseModel):
    """Base class for report parameters"""
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"

class ClinicalReportParameters(ReportParameters):
    """Parameters for clinical reports"""
    patient_ids: Optional[List[int]] = None
    doctor_ids: Optional[List[int]] = None
    procedure_types: Optional[List[str]] = None
    diagnosis_codes: Optional[List[str]] = None
    include_medical_records: bool = False
    include_prescriptions: bool = False

class FinancialReportParameters(ReportParameters):
    """Parameters for financial reports"""
    payment_status: Optional[List[str]] = None
    payment_methods: Optional[List[str]] = None
    insurance_companies: Optional[List[str]] = None
    include_taxes: bool = True
    currency: str = "BRL"

class CommercialReportParameters(ReportParameters):
    """Parameters for commercial reports"""
    procedure_ids: Optional[List[int]] = None
    estimate_status: Optional[List[str]] = None
    contract_status: Optional[List[str]] = None
    include_packages: bool = False
    include_analytics: bool = True

class AdministrativeReportParameters(ReportParameters):
    """Parameters for administrative reports"""
    department_ids: Optional[List[int]] = None
    user_roles: Optional[List[str]] = None
    include_audit_logs: bool = False
    include_performance_metrics: bool = False

class GeneratedReportBase(BaseModel):
    template_id: int
    report_type: ReportType
    report_format: ReportFormat
    parameters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

class GeneratedReportCreate(GeneratedReportBase):
    pass

class GeneratedReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    error_message: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class GeneratedReport(GeneratedReportBase):
    id: int
    report_number: str
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_count: int
    status: ReportStatus
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Schedule schemas
class ReportScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_id: int
    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    schedule_config: Optional[Dict[str, Any]] = None
    email_recipients: Optional[List[str]] = None
    notification_enabled: bool = True
    is_active: bool = True

class ReportScheduleCreate(ReportScheduleBase):
    pass

class ReportScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    schedule_config: Optional[Dict[str, Any]] = None
    email_recipients: Optional[List[str]] = None
    notification_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class ReportSchedule(ReportScheduleBase):
    id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Report Access Log schemas
class ReportAccessLogBase(BaseModel):
    report_id: int
    access_type: str = Field(..., pattern="^(view|download|print)$")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ReportAccessLogCreate(ReportAccessLogBase):
    pass

class ReportAccessLog(ReportAccessLogBase):
    id: int
    user_id: int
    accessed_at: datetime

    class Config:
        from_attributes = True

# Report Generation Request schemas
class ReportGenerationRequest(BaseModel):
    template_id: int
    report_format: ReportFormat
    parameters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    expires_in_hours: Optional[int] = Field(24, ge=1, le=168)  # 1 hour to 1 week

class BulkReportGenerationRequest(BaseModel):
    reports: List[ReportGenerationRequest]
    notify_when_complete: bool = True

# Report Analytics schemas
class ReportAnalytics(BaseModel):
    total_reports_generated: int
    reports_by_type: Dict[str, int]
    reports_by_format: Dict[str, int]
    most_used_templates: List[Dict[str, Any]]
    generation_success_rate: float
    average_generation_time_seconds: float
    total_downloads: int
    reports_generated_last_30_days: int

class ReportUsageStats(BaseModel):
    template_id: int
    template_name: str
    total_generations: int
    total_downloads: int
    last_generated: Optional[datetime] = None
    success_rate: float
    average_generation_time_seconds: float

# Report Export schemas
class ReportExportRequest(BaseModel):
    report_ids: List[int]
    export_format: ReportFormat
    include_metadata: bool = True
    compress_files: bool = False

class ReportExportResponse(BaseModel):
    export_id: str
    file_count: int
    total_size_bytes: int
    download_url: str
    expires_at: datetime

# Dashboard schemas
class ReportDashboardStats(BaseModel):
    total_templates: int
    active_schedules: int
    pending_reports: int
    completed_reports_today: int
    failed_reports_today: int
    total_downloads_today: int
    storage_used_mb: float
    most_popular_template: Optional[str] = None
    recent_reports: List[Dict[str, Any]]

# Validation schemas
class ReportValidationRequest(BaseModel):
    template_id: int
    parameters: Optional[Dict[str, Any]] = None

class ReportValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    estimated_generation_time_seconds: Optional[int] = None
    estimated_file_size_mb: Optional[float] = None
