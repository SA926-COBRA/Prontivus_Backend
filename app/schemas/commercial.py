from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class ProcedureType(str, Enum):
    SURGICAL = "surgical"
    DIAGNOSTIC = "diagnostic"
    THERAPEUTIC = "therapeutic"
    COSMETIC = "cosmetic"
    EMERGENCY = "emergency"

class EstimateStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class ContractStatus(str, Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# Base schemas
class SurgicalProcedureBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    procedure_type: ProcedureType
    category: Optional[str] = Field(None, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    base_price: float = Field(..., gt=0)
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    currency: str = Field("BRL", max_length=3)
    duration_minutes: Optional[int] = Field(None, gt=0)
    complexity_level: Optional[int] = Field(None, ge=1, le=5)
    requires_anesthesia: bool = False
    requires_hospitalization: bool = False
    recovery_days: Optional[int] = Field(None, ge=0)
    required_equipment: Optional[List[str]] = None
    required_supplies: Optional[List[str]] = None
    prerequisites: Optional[str] = None
    is_active: bool = True

    @validator('max_price')
    def validate_max_price(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v

class SurgicalProcedureCreate(SurgicalProcedureBase):
    pass

class SurgicalProcedureUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    procedure_type: Optional[ProcedureType] = None
    category: Optional[str] = Field(None, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    base_price: Optional[float] = Field(None, gt=0)
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    duration_minutes: Optional[int] = Field(None, gt=0)
    complexity_level: Optional[int] = Field(None, ge=1, le=5)
    requires_anesthesia: Optional[bool] = None
    requires_hospitalization: Optional[bool] = None
    recovery_days: Optional[int] = Field(None, ge=0)
    required_equipment: Optional[List[str]] = None
    required_supplies: Optional[List[str]] = None
    prerequisites: Optional[str] = None
    is_active: Optional[bool] = None

class SurgicalProcedure(SurgicalProcedureBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Estimate schemas
class SurgicalEstimateBase(BaseModel):
    patient_id: int
    procedure_id: int
    doctor_id: int
    estimated_date: Optional[datetime] = None
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    base_price: float = Field(..., gt=0)
    additional_fees: float = Field(0, ge=0)
    discount_percentage: float = Field(0, ge=0, le=100)
    discount_amount: float = Field(0, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=100)
    installment_count: int = Field(1, ge=1)
    insurance_covered: bool = False
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_authorization: Optional[str] = Field(None, max_length=100)
    copay_amount: float = Field(0, ge=0)
    notes: Optional[str] = None
    special_requirements: Optional[str] = None
    contraindications: Optional[str] = None
    valid_until: Optional[datetime] = None

class SurgicalEstimateCreate(SurgicalEstimateBase):
    pass

class SurgicalEstimateUpdate(BaseModel):
    estimated_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    additional_fees: Optional[float] = Field(None, ge=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=100)
    installment_count: Optional[int] = Field(None, ge=1)
    insurance_covered: Optional[bool] = None
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_authorization: Optional[str] = Field(None, max_length=100)
    copay_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    special_requirements: Optional[str] = None
    contraindications: Optional[str] = None
    valid_until: Optional[datetime] = None
    status: Optional[EstimateStatus] = None

class SurgicalEstimate(SurgicalEstimateBase):
    id: int
    estimate_number: str
    status: EstimateStatus
    total_price: float
    installment_value: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Contract schemas
class ContractPaymentSchedule(BaseModel):
    installment_number: int
    amount: float
    due_date: datetime
    status: PaymentStatus = PaymentStatus.PENDING

class SurgicalContractBase(BaseModel):
    estimate_id: Optional[int] = None
    patient_id: int
    procedure_id: int
    doctor_id: int
    contract_type: str = Field("standard", pattern="^(standard|emergency|package)$")
    total_amount: float = Field(..., gt=0)
    payment_schedule: Optional[List[ContractPaymentSchedule]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    procedure_date: Optional[datetime] = None
    terms_and_conditions: Optional[str] = None
    cancellation_policy: Optional[str] = None
    warranty_period_days: int = Field(30, ge=0)
    special_conditions: Optional[str] = None
    risk_assessment: Optional[str] = None
    post_procedure_care: Optional[str] = None

class SurgicalContractCreate(SurgicalContractBase):
    pass

class SurgicalContractUpdate(BaseModel):
    contract_type: Optional[str] = Field(None, pattern="^(standard|emergency|package)$")
    total_amount: Optional[float] = Field(None, gt=0)
    payment_schedule: Optional[List[ContractPaymentSchedule]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    procedure_date: Optional[datetime] = None
    terms_and_conditions: Optional[str] = None
    cancellation_policy: Optional[str] = None
    warranty_period_days: Optional[int] = Field(None, ge=0)
    special_conditions: Optional[str] = None
    risk_assessment: Optional[str] = None
    post_procedure_care: Optional[str] = None
    status: Optional[ContractStatus] = None
    patient_signed: Optional[bool] = None
    doctor_approved: Optional[bool] = None
    admin_approved: Optional[bool] = None

class SurgicalContract(SurgicalContractBase):
    id: int
    contract_number: str
    status: ContractStatus
    paid_amount: float
    remaining_amount: float
    payment_status: PaymentStatus
    due_dates: Optional[List[datetime]] = None
    patient_signed: bool
    patient_signature_date: Optional[datetime] = None
    doctor_approved: bool
    doctor_approval_date: Optional[datetime] = None
    admin_approved: bool
    admin_approval_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Payment schemas
class ContractPaymentBase(BaseModel):
    contract_id: int
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., max_length=50)
    payment_date: datetime
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class ContractPaymentCreate(ContractPaymentBase):
    pass

class ContractPaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_date: Optional[datetime] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[PaymentStatus] = None

class ContractPayment(ContractPaymentBase):
    id: int
    payment_number: str
    status: PaymentStatus
    processed_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Package schemas
class PackageProcedure(BaseModel):
    procedure_id: int
    quantity: int = Field(1, ge=1)
    custom_price: Optional[float] = Field(None, gt=0)

class CommercialPackageBase(BaseModel):
    package_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    procedures: List[PackageProcedure]
    total_price: float = Field(..., gt=0)
    discount_percentage: float = Field(0, ge=0, le=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    max_uses: Optional[int] = Field(None, gt=0)

class CommercialPackageCreate(CommercialPackageBase):
    pass

class CommercialPackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    procedures: Optional[List[PackageProcedure]] = None
    total_price: Optional[float] = Field(None, gt=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    max_uses: Optional[int] = Field(None, gt=0)

class CommercialPackage(CommercialPackageBase):
    id: int
    final_price: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Sales target schemas
class SalesTargetBase(BaseModel):
    target_period: str = Field(..., pattern="^(monthly|quarterly|yearly)$")
    target_year: int = Field(..., ge=2020, le=2030)
    target_month: Optional[int] = Field(None, ge=1, le=12)
    target_quarter: Optional[int] = Field(None, ge=1, le=4)
    revenue_target: float = Field(..., gt=0)
    procedure_count_target: int = Field(..., gt=0)
    contract_count_target: int = Field(..., gt=0)
    assigned_to: int

class SalesTargetCreate(SalesTargetBase):
    pass

class SalesTargetUpdate(BaseModel):
    revenue_target: Optional[float] = Field(None, gt=0)
    procedure_count_target: Optional[int] = Field(None, gt=0)
    contract_count_target: Optional[int] = Field(None, gt=0)
    current_revenue: Optional[float] = Field(None, ge=0)
    current_procedures: Optional[int] = Field(None, ge=0)
    current_contracts: Optional[int] = Field(None, ge=0)

class SalesTarget(SalesTargetBase):
    id: int
    current_revenue: float
    current_procedures: int
    current_contracts: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Dashboard and analytics schemas
class CommercialDashboardStats(BaseModel):
    total_procedures: int
    active_estimates: int
    pending_contracts: int
    monthly_revenue: float
    conversion_rate: float
    average_contract_value: float
    top_procedures: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]

class EstimateAnalytics(BaseModel):
    total_estimates: int
    converted_estimates: int
    pending_estimates: int
    expired_estimates: int
    average_conversion_time_days: float
    conversion_rate_by_procedure: List[Dict[str, Any]]

class ContractAnalytics(BaseModel):
    total_contracts: int
    active_contracts: int
    completed_contracts: int
    cancelled_contracts: int
    average_contract_value: float
    payment_completion_rate: float
    contracts_by_status: List[Dict[str, Any]]
