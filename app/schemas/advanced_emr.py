"""
Advanced EMR Pydantic Schemas
Supports controlled prescriptions, SADT, ICD-10 integration
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    DELIVERED = "delivered"
    VERIFIED = "verified"


class PrescriptionTypeCode(str, Enum):
    REGULAR = "REG"
    ANTIMICROBIAL = "ANT"
    CONTROLLED_C1 = "C1"


class SADTServiceType(str, Enum):
    EXAM = "exam"
    PROCEDURE = "procedure"
    THERAPY = "therapy"


class SADTUrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"


# ICD-10 Schemas
class ICD10CodeBase(BaseModel):
    code: str = Field(..., max_length=10)
    description: str
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class ICD10CodeCreate(ICD10CodeBase):
    pass


class ICD10CodeUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    is_active: Optional[bool] = None


class ICD10CodeInDB(ICD10CodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Patient History Schemas
class VitalSigns(BaseModel):
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class PatientHistoryBase(BaseModel):
    patient_id: int
    doctor_id: int
    visit_date: date
    visit_type: Optional[str] = Field(None, max_length=50)
    
    # Chief Complaint
    chief_complaint: Optional[str] = None
    present_illness: Optional[str] = None
    
    # Medical History
    past_medical_history: Optional[str] = None
    family_history: Optional[str] = None
    social_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    
    # Physical Examination
    vital_signs: Optional[VitalSigns] = None
    physical_exam: Optional[str] = None
    systems_review: Optional[str] = None
    
    # Assessment & Plan
    assessment: Optional[str] = None
    plan: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    
    # ICD-10 Integration
    primary_diagnosis_code: Optional[str] = Field(None, max_length=10)
    secondary_diagnosis_codes: Optional[List[str]] = None
    
    # SADT Integration
    exam_requests: Optional[List[Dict[str, Any]]] = None
    procedure_codes: Optional[List[str]] = None
    
    # Attachments
    attachments: Optional[List[Dict[str, Any]]] = None


class PatientHistoryCreate(PatientHistoryBase):
    pass


class PatientHistoryUpdate(BaseModel):
    visit_type: Optional[str] = None
    chief_complaint: Optional[str] = None
    present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    family_history: Optional[str] = None
    social_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    vital_signs: Optional[VitalSigns] = None
    physical_exam: Optional[str] = None
    systems_review: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    primary_diagnosis_code: Optional[str] = None
    secondary_diagnosis_codes: Optional[List[str]] = None
    exam_requests: Optional[List[Dict[str, Any]]] = None
    procedure_codes: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class PatientHistoryInDB(PatientHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


# Prescription Type Schemas
class PrescriptionTypeBase(BaseModel):
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=10)
    description: Optional[str] = None
    requires_special_approval: bool = False
    max_copies: int = Field(default=1, ge=1, le=3)
    is_active: bool = True


class PrescriptionTypeCreate(PrescriptionTypeBase):
    pass


class PrescriptionTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    requires_special_approval: Optional[bool] = None
    max_copies: Optional[int] = Field(None, ge=1, le=3)
    is_active: Optional[bool] = None


class PrescriptionTypeInDB(PrescriptionTypeBase):
    id: int

    class Config:
        from_attributes = True


# Prescription Medication Schemas
class PrescriptionMedicationBase(BaseModel):
    medication_name: str = Field(..., max_length=200)
    active_ingredient: Optional[str] = Field(None, max_length=200)
    concentration: Optional[str] = Field(None, max_length=100)
    pharmaceutical_form: Optional[str] = Field(None, max_length=100)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    total_quantity: Optional[str] = Field(None, max_length=100)
    administration_route: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    requires_prescription: bool = True
    controlled_substance: bool = False
    antimicrobial: bool = False


class PrescriptionMedicationCreate(PrescriptionMedicationBase):
    pass


class PrescriptionMedicationUpdate(BaseModel):
    medication_name: Optional[str] = Field(None, max_length=200)
    active_ingredient: Optional[str] = Field(None, max_length=200)
    concentration: Optional[str] = Field(None, max_length=100)
    pharmaceutical_form: Optional[str] = Field(None, max_length=100)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    total_quantity: Optional[str] = Field(None, max_length=100)
    administration_route: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    requires_prescription: Optional[bool] = None
    controlled_substance: Optional[bool] = None
    antimicrobial: Optional[bool] = None


class PrescriptionMedicationInDB(PrescriptionMedicationBase):
    id: int
    prescription_id: int

    class Config:
        from_attributes = True


# Prescription Schemas
class PrescriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    prescription_type_id: int
    issue_date: date
    valid_until: Optional[date] = None
    
    # Patient Information
    patient_name: str = Field(..., max_length=200)
    patient_cpf: Optional[str] = Field(None, max_length=14)
    patient_dob: Optional[date] = None
    
    # Doctor Information
    doctor_name: str = Field(..., max_length=200)
    doctor_crm: str = Field(..., max_length=20)
    doctor_crm_state: str = Field(..., max_length=2)
    clinic_name: Optional[str] = Field(None, max_length=200)
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = Field(None, max_length=20)
    
    # Prescription Content
    medications: List[PrescriptionMedicationCreate]
    instructions: Optional[str] = None
    observations: Optional[str] = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    valid_until: Optional[date] = None
    medications: Optional[List[PrescriptionMedicationCreate]] = None
    instructions: Optional[str] = None
    observations: Optional[str] = None
    clinic_name: Optional[str] = Field(None, max_length=200)
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = Field(None, max_length=20)


class PrescriptionInDB(PrescriptionBase):
    id: int
    prescription_number: str
    is_digitally_signed: bool = False
    certificate_serial: Optional[str] = Field(None, max_length=200)
    signature_timestamp: Optional[datetime] = None
    signature_hash: Optional[str] = Field(None, max_length=500)
    signature_valid: bool = False
    qr_code_data: Optional[str] = Field(None, max_length=500)
    verification_url: Optional[str] = Field(None, max_length=500)
    pdf_path: Optional[str] = Field(None, max_length=500)
    pdf_generated_at: Optional[datetime] = None
    status: PrescriptionStatus = PrescriptionStatus.DRAFT
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# SADT Request Schemas
class SADTRequestBase(BaseModel):
    patient_id: int
    doctor_id: int
    medical_history_id: Optional[int] = None
    request_date: date
    service_type: SADTServiceType
    service_category: Optional[str] = Field(None, max_length=100)
    service_name: str = Field(..., max_length=200)
    service_code: Optional[str] = Field(None, max_length=50)
    service_description: Optional[str] = None
    clinical_indication: str
    clinical_question: Optional[str] = None
    urgency_level: SADTUrgencyLevel = SADTUrgencyLevel.ROUTINE
    health_plan_id: Optional[int] = None
    authorization_number: Optional[str] = Field(None, max_length=100)
    authorization_status: Optional[str] = Field(None, max_length=20)


class SADTRequestCreate(SADTRequestBase):
    pass


class SADTRequestUpdate(BaseModel):
    service_category: Optional[str] = Field(None, max_length=100)
    service_name: Optional[str] = Field(None, max_length=200)
    service_code: Optional[str] = Field(None, max_length=50)
    service_description: Optional[str] = None
    clinical_indication: Optional[str] = None
    clinical_question: Optional[str] = None
    urgency_level: Optional[SADTUrgencyLevel] = None
    health_plan_id: Optional[int] = None
    authorization_number: Optional[str] = Field(None, max_length=100)
    authorization_status: Optional[str] = Field(None, max_length=20)


class SADTRequestInDB(SADTRequestBase):
    id: int
    request_number: str
    status: str = "draft"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Prescription Audit Log Schemas
class PrescriptionAuditLogBase(BaseModel):
    prescription_id: int
    user_id: int
    action: str = Field(..., max_length=50)
    description: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)


class PrescriptionAuditLogCreate(PrescriptionAuditLogBase):
    pass


class PrescriptionAuditLogInDB(PrescriptionAuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Response Schemas
class PrescriptionWithDetails(PrescriptionInDB):
    medications: List[PrescriptionMedicationInDB]
    prescription_type: PrescriptionTypeInDB
    patient: Optional[Dict[str, Any]] = None
    doctor: Optional[Dict[str, Any]] = None


class PatientHistoryWithDetails(PatientHistoryInDB):
    primary_diagnosis: Optional[ICD10CodeInDB] = None
    secondary_diagnoses: Optional[List[ICD10CodeInDB]] = None
    patient: Optional[Dict[str, Any]] = None
    doctor: Optional[Dict[str, Any]] = None


class SADTRequestWithDetails(SADTRequestInDB):
    patient: Optional[Dict[str, Any]] = None
    doctor: Optional[Dict[str, Any]] = None
    medical_history: Optional[PatientHistoryInDB] = None
    health_plan: Optional[Dict[str, Any]] = None


# Search and Filter Schemas
class PatientHistorySearch(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    diagnosis_code: Optional[str] = None
    visit_type: Optional[str] = None


class PrescriptionSearch(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    prescription_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[PrescriptionStatus] = None
    is_signed: Optional[bool] = None


class SADTRequestSearch(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    service_type: Optional[SADTServiceType] = None
    urgency_level: Optional[SADTUrgencyLevel] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[str] = None