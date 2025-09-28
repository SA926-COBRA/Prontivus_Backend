"""
Digital Prescription Schemas
Pydantic schemas for digital prescription with ICP-Brasil signature
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PrescriptionType(str, Enum):
    COMMON = "common"
    ANTIMICROBIAL = "antimicrobial"
    CONTROLLED_C1 = "controlled_c1"
    CONTROLLED_C2 = "controlled_c2"
    CONTROLLED_C3 = "controlled_c3"
    CONTROLLED_C4 = "controlled_c4"
    CONTROLLED_C5 = "controlled_c5"


class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SignatureType(str, Enum):
    A1 = "a1"
    A3 = "a3"
    CLOUD = "cloud"


# Medication schemas
class PrescriptionMedicationBase(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=255)
    active_ingredient: Optional[str] = Field(None, max_length=255)
    dosage_form: Optional[str] = Field(None, max_length=100)
    strength: Optional[str] = Field(None, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    route: Optional[str] = Field(None, max_length=100)
    instructions: Optional[str] = None
    anvisa_registration: Optional[str] = Field(None, max_length=50)
    controlled_substance: bool = False
    controlled_class: Optional[str] = Field(None, max_length=10)
    quantity: Optional[int] = Field(None, ge=1)
    refills_allowed: int = Field(0, ge=0)
    order_index: int = Field(0, ge=0)


class PrescriptionMedicationCreate(PrescriptionMedicationBase):
    pass


class PrescriptionMedication(PrescriptionMedicationBase):
    id: int
    prescription_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Main prescription schemas
class DigitalPrescriptionBase(BaseModel):
    appointment_id: Optional[int] = None
    doctor_id: int
    patient_id: int
    prescription_type: PrescriptionType
    prescription_data: Dict[str, Any]
    prescription_text: Optional[str] = None
    signature_type: Optional[SignatureType] = None
    delivery_method: Optional[str] = Field(None, max_length=50)
    delivery_recipient: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None


class DigitalPrescriptionCreate(DigitalPrescriptionBase):
    medications: List[PrescriptionMedicationCreate] = Field(..., min_items=1)


class DigitalPrescriptionUpdate(BaseModel):
    prescription_data: Optional[Dict[str, Any]] = None
    prescription_text: Optional[str] = None
    status: Optional[PrescriptionStatus] = None
    delivery_method: Optional[str] = Field(None, max_length=50)
    delivery_recipient: Optional[str] = Field(None, max_length=255)
    delivery_status: Optional[str] = Field(None, max_length=20)
    is_valid: Optional[bool] = None
    validation_errors: Optional[Dict[str, Any]] = None


class DigitalPrescription(DigitalPrescriptionBase):
    id: int
    tenant_id: int
    prescription_id: str
    status: PrescriptionStatus
    certificate_serial: Optional[str] = None
    signature_hash: Optional[str] = None
    signature_timestamp: Optional[datetime] = None
    signature_valid_until: Optional[datetime] = None
    pdf_path: Optional[str] = None
    pdf_hash: Optional[str] = None
    qr_code_url: Optional[str] = None
    delivery_status: str
    delivery_timestamp: Optional[datetime] = None
    is_valid: bool
    validation_timestamp: Optional[datetime] = None
    validation_errors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Configuration schemas
class PrescriptionConfigurationBase(BaseModel):
    is_enabled: bool = False
    clinic_name: str = Field(..., min_length=1, max_length=255)
    clinic_cnpj: Optional[str] = Field(None, max_length=18)
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = Field(None, max_length=20)
    clinic_email: Optional[str] = Field(None, max_length=255)
    signature_enabled: bool = True
    default_signature_type: SignatureType = SignatureType.A1
    certificate_path: Optional[str] = Field(None, max_length=500)
    certificate_password: Optional[str] = Field(None, max_length=255)
    pdf_template: str = "standard"
    include_clinic_logo: bool = True
    logo_path: Optional[str] = Field(None, max_length=500)
    include_qr_code: bool = True
    enforce_anvisa_rules: bool = True
    require_controlled_substance_justification: bool = True
    max_prescription_validity_days: int = Field(30, ge=1, le=365)
    default_delivery_method: str = "email"
    auto_send_prescription: bool = False
    send_to_patient_portal: bool = True
    notify_doctor_on_delivery: bool = True
    notify_patient_on_ready: bool = True
    encrypt_prescriptions: bool = True
    audit_all_access: bool = True
    retention_days: int = Field(365, ge=30, le=2555)  # 30 days to 7 years
    integrate_with_pharmacy: bool = False
    pharmacy_api_endpoint: Optional[str] = Field(None, max_length=500)
    pharmacy_api_key: Optional[str] = Field(None, max_length=255)


class PrescriptionConfigurationCreate(PrescriptionConfigurationBase):
    pass


class PrescriptionConfigurationUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    clinic_name: Optional[str] = Field(None, min_length=1, max_length=255)
    clinic_cnpj: Optional[str] = Field(None, max_length=18)
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = Field(None, max_length=20)
    clinic_email: Optional[str] = Field(None, max_length=255)
    signature_enabled: Optional[bool] = None
    default_signature_type: Optional[SignatureType] = None
    certificate_path: Optional[str] = Field(None, max_length=500)
    certificate_password: Optional[str] = Field(None, max_length=255)
    pdf_template: Optional[str] = None
    include_clinic_logo: Optional[bool] = None
    logo_path: Optional[str] = Field(None, max_length=500)
    include_qr_code: Optional[bool] = None
    enforce_anvisa_rules: Optional[bool] = None
    require_controlled_substance_justification: Optional[bool] = None
    max_prescription_validity_days: Optional[int] = Field(None, ge=1, le=365)
    default_delivery_method: Optional[str] = Field(None, max_length=50)
    auto_send_prescription: Optional[bool] = None
    send_to_patient_portal: Optional[bool] = None
    notify_doctor_on_delivery: Optional[bool] = None
    notify_patient_on_ready: Optional[bool] = None
    encrypt_prescriptions: Optional[bool] = None
    audit_all_access: Optional[bool] = None
    retention_days: Optional[int] = Field(None, ge=30, le=2555)
    integrate_with_pharmacy: Optional[bool] = None
    pharmacy_api_endpoint: Optional[str] = Field(None, max_length=500)
    pharmacy_api_key: Optional[str] = Field(None, max_length=255)


class PrescriptionConfiguration(PrescriptionConfigurationBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Specialized schemas for API requests
class PrescriptionSignRequest(BaseModel):
    """Request to sign a prescription"""
    prescription_id: str
    signature_type: SignatureType
    certificate_password: Optional[str] = None
    certificate_file: Optional[str] = None  # Base64 encoded certificate


class PrescriptionSignResponse(BaseModel):
    """Response from prescription signing"""
    success: bool
    prescription_id: str
    signature_hash: Optional[str] = None
    pdf_path: Optional[str] = None
    qr_code_url: Optional[str] = None
    message: Optional[str] = None


class PrescriptionDeliveryRequest(BaseModel):
    """Request to deliver a prescription"""
    prescription_id: str
    delivery_method: str
    delivery_recipient: str
    message: Optional[str] = None


class PrescriptionDeliveryResponse(BaseModel):
    """Response from prescription delivery"""
    success: bool
    prescription_id: str
    delivery_status: str
    delivery_timestamp: Optional[datetime] = None
    message: Optional[str] = None


class PrescriptionVerificationRequest(BaseModel):
    """Request to verify a prescription"""
    verification_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PrescriptionVerificationResponse(BaseModel):
    """Response from prescription verification"""
    success: bool
    is_valid: bool
    prescription_id: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    prescription_date: Optional[datetime] = None
    signature_valid: Optional[bool] = None
    verification_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Template schemas
class PrescriptionTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    specialty: Optional[str] = Field(None, max_length=100)
    template_data: Dict[str, Any]
    template_text: Optional[str] = None
    tags: Optional[List[str]] = None


class PrescriptionTemplateCreate(PrescriptionTemplateBase):
    pass


class PrescriptionTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    specialty: Optional[str] = Field(None, max_length=100)
    template_data: Optional[Dict[str, Any]] = None
    template_text: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class PrescriptionTemplate(PrescriptionTemplateBase):
    id: int
    tenant_id: int
    usage_count: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Analytics schemas
class PrescriptionAnalyticsBase(BaseModel):
    date: datetime
    period_type: str = "daily"
    total_prescriptions: int = 0
    signed_prescriptions: int = 0
    delivered_prescriptions: int = 0
    cancelled_prescriptions: int = 0
    common_prescriptions: int = 0
    antimicrobial_prescriptions: int = 0
    controlled_prescriptions: int = 0
    email_deliveries: int = 0
    whatsapp_deliveries: int = 0
    portal_deliveries: int = 0
    link_deliveries: int = 0
    total_verifications: int = 0
    successful_verifications: int = 0
    failed_verifications: int = 0


class PrescriptionAnalyticsCreate(PrescriptionAnalyticsBase):
    pass


class PrescriptionAnalytics(PrescriptionAnalyticsBase):
    id: int
    tenant_id: int
    prescriptions_by_doctor: Optional[Dict[str, int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard schemas
class PrescriptionDashboardResponse(BaseModel):
    """Prescription dashboard response"""
    total_prescriptions: int
    signed_prescriptions: int
    pending_signatures: int
    delivered_today: int
    prescriptions_this_month: int
    average_prescriptions_per_day: float
    most_prescribed_medications: List[Dict[str, Any]]
    prescriptions_by_type: Dict[str, int]
    delivery_methods_breakdown: Dict[str, int]
    recent_prescriptions: List[Dict[str, Any]]


class PrescriptionSummary(BaseModel):
    """Summary of a prescription"""
    id: int
    prescription_id: str
    doctor_name: str
    patient_name: str
    prescription_type: str
    status: str
    medication_count: int
    created_at: datetime
    signed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    is_valid: bool


class PrescriptionsResponse(BaseModel):
    """Response with list of prescriptions"""
    prescriptions: List[PrescriptionSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
