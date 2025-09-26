from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

# Enums
class PrescriptionControlLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    M1 = "M1"
    M2 = "M2"

class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SADTType(str, Enum):
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    SURGERY = "surgery"
    EXAMINATION = "examination"
    THERAPY = "therapy"
    EMERGENCY = "emergency"

class SADTStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class ICDCategory(str, Enum):
    DISEASE = "disease"
    INJURY = "injury"
    EXTERNAL_CAUSE = "external_cause"
    PROCEDURE = "procedure"
    SYMPTOM = "symptom"
    SIGN = "sign"

# Controlled Prescription schemas
class ControlledPrescriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    medication_name: str = Field(..., min_length=1, max_length=200)
    generic_name: Optional[str] = Field(None, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    control_level: PrescriptionControlLevel
    anvisa_code: Optional[str] = Field(None, max_length=50)
    controlled_substance: bool = False
    requires_special_authorization: bool = False
    prescription_date: datetime
    valid_until: Optional[datetime] = None
    refills_allowed: int = Field(0, ge=0)
    instructions: Optional[str] = None
    side_effects: Optional[str] = None
    contraindications: Optional[str] = None
    interactions: Optional[str] = None

class ControlledPrescriptionCreate(ControlledPrescriptionBase):
    pass

class ControlledPrescriptionUpdate(BaseModel):
    medication_name: Optional[str] = Field(None, min_length=1, max_length=200)
    generic_name: Optional[str] = Field(None, max_length=200)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=1, max_length=100)
    duration: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    control_level: Optional[PrescriptionControlLevel] = None
    anvisa_code: Optional[str] = Field(None, max_length=50)
    controlled_substance: Optional[bool] = None
    requires_special_authorization: Optional[bool] = None
    valid_until: Optional[datetime] = None
    refills_allowed: Optional[int] = Field(None, ge=0)
    status: Optional[PrescriptionStatus] = None
    instructions: Optional[str] = None
    side_effects: Optional[str] = None
    contraindications: Optional[str] = None
    interactions: Optional[str] = None

class ControlledPrescription(ControlledPrescriptionBase):
    id: int
    prescription_number: str
    refills_used: int
    status: PrescriptionStatus
    dispensed: bool
    dispensed_at: Optional[datetime] = None
    dispensed_by: Optional[int] = None
    digital_signature: Optional[str] = None
    prescription_hash: Optional[str] = None
    regulatory_compliance: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# Prescription Refill schemas
class PrescriptionRefillBase(BaseModel):
    prescription_id: int
    refill_number: int = Field(..., gt=0)
    refill_date: datetime
    quantity_dispensed: int = Field(..., gt=0)
    dispensed_by: int
    pharmacy_name: Optional[str] = Field(None, max_length=200)
    pharmacy_address: Optional[str] = None
    patient_identification_verified: bool = False
    prescription_verified: bool = False
    regulatory_compliance_checked: bool = False

class PrescriptionRefillCreate(PrescriptionRefillBase):
    pass

class PrescriptionRefill(PrescriptionRefillBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# SADT schemas
class SADTBase(BaseModel):
    patient_id: int
    doctor_id: int
    sadt_type: SADTType
    procedure_name: str = Field(..., min_length=1, max_length=200)
    procedure_code: Optional[str] = Field(None, max_length=50)
    description: str
    clinical_indication: str
    medical_history: Optional[str] = None
    current_symptoms: Optional[str] = None
    physical_examination: Optional[str] = None
    diagnostic_hypothesis: str
    requested_date: datetime
    scheduled_date: Optional[datetime] = None
    priority: str = Field("normal", regex="^(low|normal|high|urgent)$")
    estimated_duration: Optional[int] = Field(None, gt=0)
    health_plan_id: Optional[int] = None
    copayment_required: bool = False
    copayment_amount: Optional[Decimal] = Field(None, ge=0)
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None

class SADTCreate(SADTBase):
    pass

class SADTUpdate(BaseModel):
    sadt_type: Optional[SADTType] = None
    procedure_name: Optional[str] = Field(None, min_length=1, max_length=200)
    procedure_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    clinical_indication: Optional[str] = None
    medical_history: Optional[str] = None
    current_symptoms: Optional[str] = None
    physical_examination: Optional[str] = None
    diagnostic_hypothesis: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[SADTStatus] = None
    priority: Optional[str] = Field(None, regex="^(low|normal|high|urgent)$")
    estimated_duration: Optional[int] = Field(None, gt=0)
    health_plan_id: Optional[int] = None
    copayment_required: Optional[bool] = None
    copayment_amount: Optional[Decimal] = Field(None, ge=0)
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None

class SADT(SADTBase):
    id: int
    sadt_number: str
    authorized_date: Optional[datetime] = None
    authorized_by: Optional[int] = None
    authorization_number: Optional[str] = None
    status: SADTStatus
    health_plan_authorization: Optional[str] = None
    procedure_results: Optional[str] = None
    regulatory_compliance: Optional[Dict[str, Any]] = None
    required_documents: Optional[Dict[str, Any]] = None
    attached_documents: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True

# SADT ICD Code schemas
class SADTICDCodeBase(BaseModel):
    sadt_id: int
    icd_code: str = Field(..., min_length=1, max_length=20)
    icd_category: ICDCategory
    icd_description: str = Field(..., min_length=1, max_length=500)
    is_primary: bool = False
    severity: Optional[str] = Field(None, max_length=50)
    laterality: Optional[str] = Field(None, regex="^(Left|Right|Bilateral)$")
    episode_type: Optional[str] = Field(None, regex="^(Initial|Subsequent|Sequela)$")

class SADTICDCodeCreate(SADTICDCodeBase):
    pass

class SADTICDCodeUpdate(BaseModel):
    icd_code: Optional[str] = Field(None, min_length=1, max_length=20)
    icd_category: Optional[ICDCategory] = None
    icd_description: Optional[str] = Field(None, min_length=1, max_length=500)
    is_primary: Optional[bool] = None
    severity: Optional[str] = Field(None, max_length=50)
    laterality: Optional[str] = Field(None, regex="^(Left|Right|Bilateral)$")
    episode_type: Optional[str] = Field(None, regex="^(Initial|Subsequent|Sequela)$")

class SADTICDCode(SADTICDCodeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ICD Code schemas
class ICDCodeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=1, max_length=500)
    category: ICDCategory
    parent_code: Optional[str] = Field(None, max_length=20)
    is_leaf: bool = True
    level: int = Field(1, ge=1)
    cid10_code: Optional[str] = Field(None, max_length=20)
    cid10_description: Optional[str] = Field(None, max_length=500)

class ICDCodeCreate(ICDCodeBase):
    pass

class ICDCodeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[ICDCategory] = None
    parent_code: Optional[str] = Field(None, max_length=20)
    is_leaf: Optional[bool] = None
    level: Optional[int] = Field(None, ge=1)
    cid10_code: Optional[str] = Field(None, max_length=20)
    cid10_description: Optional[str] = Field(None, max_length=500)

class ICDCode(ICDCodeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Medical Procedure schemas
class MedicalProcedureBase(BaseModel):
    tuss_code: str = Field(..., min_length=1, max_length=50)
    procedure_name: str = Field(..., min_length=1, max_length=200)
    description: str
    procedure_type: SADTType
    specialty: Optional[str] = Field(None, max_length=100)
    complexity: Optional[str] = Field(None, regex="^(Simple|Medium|Complex)$")
    base_value: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("BRL", max_length=3)
    anvisa_authorization: bool = False
    cff_authorization: bool = False
    crm_authorization: bool = False
    minimum_qualification: Optional[str] = Field(None, max_length=100)
    required_equipment: Optional[Dict[str, Any]] = None
    contraindications: Optional[str] = None
    effective_date: date
    expiry_date: Optional[date] = None

class MedicalProcedureCreate(MedicalProcedureBase):
    pass

class MedicalProcedureUpdate(BaseModel):
    tuss_code: Optional[str] = Field(None, min_length=1, max_length=50)
    procedure_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    procedure_type: Optional[SADTType] = None
    specialty: Optional[str] = Field(None, max_length=100)
    complexity: Optional[str] = Field(None, regex="^(Simple|Medium|Complex)$")
    base_value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    anvisa_authorization: Optional[bool] = None
    cff_authorization: Optional[bool] = None
    crm_authorization: Optional[bool] = None
    minimum_qualification: Optional[str] = Field(None, max_length=100)
    required_equipment: Optional[Dict[str, Any]] = None
    contraindications: Optional[str] = None
    is_active: Optional[bool] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None

class MedicalProcedure(MedicalProcedureBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Health Plan schemas
class HealthPlanBase(BaseModel):
    plan_name: str = Field(..., min_length=1, max_length=200)
    plan_code: str = Field(..., min_length=1, max_length=50)
    plan_type: str = Field(..., min_length=1, max_length=100)
    coverage_type: str = Field(..., min_length=1, max_length=100)
    requires_authorization: bool = True
    authorization_timeframe: Optional[int] = Field(None, gt=0)
    emergency_authorization: bool = False
    copayment_required: bool = False
    copayment_percentage: Optional[float] = Field(None, ge=0, le=100)
    annual_limit: Optional[Decimal] = Field(None, ge=0)
    procedure_limit: Optional[Decimal] = Field(None, ge=0)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    effective_date: date
    expiry_date: Optional[date] = None

class HealthPlanCreate(HealthPlanBase):
    pass

class HealthPlanUpdate(BaseModel):
    plan_name: Optional[str] = Field(None, min_length=1, max_length=200)
    plan_code: Optional[str] = Field(None, min_length=1, max_length=50)
    plan_type: Optional[str] = Field(None, min_length=1, max_length=100)
    coverage_type: Optional[str] = Field(None, min_length=1, max_length=100)
    requires_authorization: Optional[bool] = None
    authorization_timeframe: Optional[int] = Field(None, gt=0)
    emergency_authorization: Optional[bool] = None
    copayment_required: Optional[bool] = None
    copayment_percentage: Optional[float] = Field(None, ge=0, le=100)
    annual_limit: Optional[Decimal] = Field(None, ge=0)
    procedure_limit: Optional[Decimal] = Field(None, ge=0)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None

class HealthPlan(HealthPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Audit schemas
class PrescriptionAuditBase(BaseModel):
    prescription_id: int
    action: str = Field(..., min_length=1, max_length=50)
    previous_status: Optional[str] = Field(None, max_length=50)
    new_status: Optional[str] = Field(None, max_length=50)
    performed_by: int
    reason: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None

class PrescriptionAuditCreate(PrescriptionAuditBase):
    pass

class PrescriptionAudit(PrescriptionAuditBase):
    id: int
    performed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class SADTAuditBase(BaseModel):
    sadt_id: int
    action: str = Field(..., min_length=1, max_length=50)
    previous_status: Optional[str] = Field(None, max_length=50)
    new_status: Optional[str] = Field(None, max_length=50)
    performed_by: int
    reason: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None

class SADTAuditCreate(SADTAuditBase):
    pass

class SADTAudit(SADTAuditBase):
    id: int
    performed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Request/Response schemas
class PrescriptionSearchRequest(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    control_level: Optional[PrescriptionControlLevel] = None
    status: Optional[PrescriptionStatus] = None
    medication_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class SADTSearchRequest(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    sadt_type: Optional[SADTType] = None
    status: Optional[SADTStatus] = None
    procedure_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class ICDCodeSearchRequest(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ICDCategory] = None
    parent_code: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class PrescriptionDispenseRequest(BaseModel):
    prescription_id: int
    quantity_dispensed: int = Field(..., gt=0)
    pharmacy_name: Optional[str] = None
    pharmacy_address: Optional[str] = None
    patient_identification_verified: bool = True
    prescription_verified: bool = True
    regulatory_compliance_checked: bool = True

class SADTAuthorizationRequest(BaseModel):
    sadt_id: int
    authorization_number: str
    authorized_by: int
    authorized_date: datetime
    procedure_results: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None

class PrescriptionSummary(BaseModel):
    total_prescriptions: int
    active_prescriptions: int
    controlled_prescriptions: int
    expired_prescriptions: int
    prescriptions_by_control_level: Dict[str, int]
    prescriptions_by_status: Dict[str, int]

class SADTSummary(BaseModel):
    total_sadt: int
    pending_sadt: int
    authorized_sadt: int
    completed_sadt: int
    sadt_by_type: Dict[str, int]
    sadt_by_status: Dict[str, int]

class ICDCodeHierarchy(BaseModel):
    code: str
    description: str
    category: ICDCategory
    level: int
    children: List['ICDCodeHierarchy'] = []
    parent: Optional['ICDCodeHierarchy'] = None

    class Config:
        from_attributes = True

# Update forward references
ICDCodeHierarchy.model_rebuild()
