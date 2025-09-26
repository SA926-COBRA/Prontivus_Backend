from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class TISSCategory(str, Enum):
    MEDICAL_CONSULTATION = "medical_consultation"
    SURGICAL_PROCEDURE = "surgical_procedure"
    DIAGNOSTIC_EXAM = "diagnostic_exam"
    THERAPEUTIC_PROCEDURE = "therapeutic_procedure"
    EMERGENCY_CARE = "emergency_care"
    HOSPITALIZATION = "hospitalization"
    OUTPATIENT_CARE = "outpatient_care"

class TISSStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PAID = "paid"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# TISS Code schemas
class TISSCodeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=1, max_length=500)
    category: TISSCategory
    base_value: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("BRL", max_length=3)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    anvisa_authorization: bool = False
    cff_authorization: bool = False
    crm_authorization: bool = False
    tiss_version: str = Field(..., min_length=1, max_length=10)
    effective_date: date
    expiry_date: Optional[date] = None
    requirements: Optional[str] = None
    contraindications: Optional[str] = None
    notes: Optional[str] = None

class TISSCodeCreate(TISSCodeBase):
    pass

class TISSCodeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[TISSCategory] = None
    base_value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    anvisa_authorization: Optional[bool] = None
    cff_authorization: Optional[bool] = None
    crm_authorization: Optional[bool] = None
    tiss_version: Optional[str] = Field(None, min_length=1, max_length=10)
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    requirements: Optional[str] = None
    contraindications: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class TISSCode(TISSCodeBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# TISS Procedure schemas
class TISSProcedureBase(BaseModel):
    patient_id: int
    doctor_id: int
    tiss_code_id: int
    procedure_date: datetime
    procedure_time: Optional[int] = Field(None, gt=0)
    medical_indication: str
    procedure_description: Optional[str] = None
    results: Optional[str] = None
    complications: Optional[str] = None
    base_value: Decimal = Field(..., ge=0)
    discount_percentage: float = Field(0.0, ge=0, le=100)
    discount_amount: Decimal = Field(0.0, ge=0)
    final_value: Decimal = Field(..., ge=0)
    currency: str = Field("BRL", max_length=3)
    health_plan_id: Optional[int] = None
    authorization_number: Optional[str] = Field(None, max_length=50)
    copayment_required: bool = False
    copayment_amount: Optional[Decimal] = Field(None, ge=0)

class TISSProcedureCreate(TISSProcedureBase):
    pass

class TISSProcedureUpdate(BaseModel):
    procedure_time: Optional[int] = Field(None, gt=0)
    medical_indication: Optional[str] = None
    procedure_description: Optional[str] = None
    results: Optional[str] = None
    complications: Optional[str] = None
    base_value: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    final_value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    health_plan_id: Optional[int] = None
    authorization_number: Optional[str] = Field(None, max_length=50)
    copayment_required: Optional[bool] = None
    copayment_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[TISSStatus] = None
    payment_status: Optional[PaymentStatus] = None

class TISSProcedure(TISSProcedureBase):
    id: int
    procedure_number: str
    status: TISSStatus
    payment_status: PaymentStatus
    tiss_submission_id: Optional[str] = None
    tiss_response: Optional[Dict[str, Any]] = None
    tiss_errors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Invoice schemas
class InvoiceBase(BaseModel):
    procedure_id: int
    patient_id: int
    health_plan_id: Optional[int] = None
    invoice_date: date
    due_date: date
    payment_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(0.0, ge=0)
    tax_amount: Decimal = Field(0.0, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    paid_amount: Decimal = Field(0.0, ge=0)
    currency: str = Field("BRL", max_length=3)
    notes: Optional[str] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    subtotal: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[InvoiceStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)

class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    status: InvoiceStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    invoice_id: int
    patient_id: int
    payment_date: datetime
    amount: Decimal = Field(..., ge=0)
    currency: str = Field("BRL", max_length=3)
    payment_method: str = Field(..., min_length=1, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    processed_by: Optional[int] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    payment_date: Optional[datetime] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[str] = Field(None, min_length=1, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    processed_by: Optional[int] = None

class Payment(PaymentBase):
    id: int
    payment_number: str
    status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Financial Report schemas
class FinancialReportBase(BaseModel):
    report_name: str = Field(..., min_length=1, max_length=200)
    report_type: str = Field(..., min_length=1, max_length=50)
    period_start: date
    period_end: date
    total_procedures: int = Field(0, ge=0)
    total_revenue: Decimal = Field(0.0, ge=0)
    total_payments: Decimal = Field(0.0, ge=0)
    total_outstanding: Decimal = Field(0.0, ge=0)
    revenue_by_category: Optional[Dict[str, Any]] = None
    payments_by_method: Optional[Dict[str, Any]] = None
    outstanding_by_health_plan: Optional[Dict[str, Any]] = None
    report_data: Dict[str, Any]

class FinancialReportCreate(FinancialReportBase):
    pass

class FinancialReport(FinancialReportBase):
    id: int
    generated_at: datetime
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# TISS Integration schemas
class TISSIntegrationBase(BaseModel):
    integration_name: str = Field(..., min_length=1, max_length=100)
    health_plan_id: int
    api_endpoint: str = Field(..., min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, max_length=200)
    api_secret: Optional[str] = Field(None, max_length=200)
    tiss_version: str = Field(..., min_length=1, max_length=10)
    submission_frequency: str = Field("daily", regex="^(daily|weekly|monthly)$")
    auto_submission: bool = True

class TISSIntegrationCreate(TISSIntegrationBase):
    pass

class TISSIntegrationUpdate(BaseModel):
    integration_name: Optional[str] = Field(None, min_length=1, max_length=100)
    health_plan_id: Optional[int] = None
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, max_length=200)
    api_secret: Optional[str] = Field(None, max_length=200)
    tiss_version: Optional[str] = Field(None, min_length=1, max_length=10)
    submission_frequency: Optional[str] = Field(None, regex="^(daily|weekly|monthly)$")
    auto_submission: Optional[bool] = None
    is_active: Optional[bool] = None

class TISSIntegration(TISSIntegrationBase):
    id: int
    is_active: bool
    last_sync: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# TISS Submission schemas
class TISSSubmissionBase(BaseModel):
    integration_id: int
    procedure_id: Optional[int] = None
    submission_date: datetime
    submission_type: str = Field(..., min_length=1, max_length=50)
    tiss_xml: Optional[str] = None
    tiss_response: Optional[str] = None
    tiss_status: Optional[str] = Field(None, max_length=50)
    tiss_message: Optional[str] = None
    error_code: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None
    retry_count: int = Field(0, ge=0)
    max_retries: int = Field(3, ge=0)

class TISSSubmissionCreate(TISSSubmissionBase):
    pass

class TISSSubmissionUpdate(BaseModel):
    tiss_response: Optional[str] = None
    tiss_status: Optional[str] = Field(None, max_length=50)
    tiss_message: Optional[str] = None
    status: Optional[TISSStatus] = None
    processed_at: Optional[datetime] = None
    error_code: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)

class TISSSubmission(TISSSubmissionBase):
    id: int
    submission_id: str
    status: TISSStatus
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Health Plan Financial schemas
class HealthPlanFinancialBase(BaseModel):
    health_plan_id: int
    contract_number: Optional[str] = Field(None, max_length=100)
    contract_start_date: date
    contract_end_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    discount_percentage: float = Field(0.0, ge=0, le=100)
    copayment_percentage: float = Field(0.0, ge=0, le=100)
    annual_limit: Optional[Decimal] = Field(None, ge=0)
    procedure_limit: Optional[Decimal] = Field(None, ge=0)
    monthly_cap: Optional[Decimal] = Field(None, ge=0)
    current_balance: Decimal = Field(0.0, ge=0)
    outstanding_amount: Decimal = Field(0.0, ge=0)
    last_payment_date: Optional[date] = None

class HealthPlanFinancialCreate(HealthPlanFinancialBase):
    pass

class HealthPlanFinancialUpdate(BaseModel):
    contract_number: Optional[str] = Field(None, max_length=100)
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    copayment_percentage: Optional[float] = Field(None, ge=0, le=100)
    annual_limit: Optional[Decimal] = Field(None, ge=0)
    procedure_limit: Optional[Decimal] = Field(None, ge=0)
    monthly_cap: Optional[Decimal] = Field(None, ge=0)
    current_balance: Optional[Decimal] = Field(None, ge=0)
    outstanding_amount: Optional[Decimal] = Field(None, ge=0)
    last_payment_date: Optional[date] = None
    is_active: Optional[bool] = None

class HealthPlanFinancial(HealthPlanFinancialBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Request/Response schemas
class TISSCodeSearchRequest(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TISSCategory] = None
    tiss_version: Optional[str] = None
    is_active: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class TISSProcedureSearchRequest(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    tiss_code_id: Optional[int] = None
    status: Optional[TISSStatus] = None
    payment_status: Optional[PaymentStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class InvoiceSearchRequest(BaseModel):
    patient_id: Optional[int] = None
    health_plan_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    payment_status: Optional[PaymentStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class PaymentSearchRequest(BaseModel):
    patient_id: Optional[int] = None
    invoice_id: Optional[int] = None
    status: Optional[PaymentStatus] = None
    payment_method: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class TISSSubmissionRequest(BaseModel):
    procedure_id: int
    integration_id: int
    submission_type: str = "procedure"

class FinancialSummary(BaseModel):
    total_procedures: int
    total_revenue: Decimal
    total_payments: Decimal
    total_outstanding: Decimal
    procedures_by_status: Dict[str, int]
    revenue_by_category: Dict[str, Decimal]
    payments_by_method: Dict[str, Decimal]
    outstanding_by_health_plan: Dict[str, Decimal]

class TISSDashboardSummary(BaseModel):
    total_submissions: int
    successful_submissions: int
    failed_submissions: int
    pending_submissions: int
    submissions_by_status: Dict[str, int]
    recent_submissions: List[Dict[str, Any]]
    integration_status: Dict[str, Any]
