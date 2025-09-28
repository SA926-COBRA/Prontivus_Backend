"""
Digital Prescription Models
Models for digital prescription with ICP-Brasil signature
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class PrescriptionType(str, enum.Enum):
    """Types of prescriptions"""
    COMMON = "common"  # Receita comum
    ANTIMICROBIAL = "antimicrobial"  # Antimicrobianos (RDC 471/2021)
    CONTROLLED_C1 = "controlled_c1"  # Substâncias controladas C1 (duas vias)
    CONTROLLED_C2 = "controlled_c2"  # Substâncias controladas C2
    CONTROLLED_C3 = "controlled_c3"  # Substâncias controladas C3
    CONTROLLED_C4 = "controlled_c4"  # Substâncias controladas C4
    CONTROLLED_C5 = "controlled_c5"  # Substâncias controladas C5


class PrescriptionStatus(str, enum.Enum):
    """Prescription status"""
    DRAFT = "draft"
    SIGNED = "signed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SignatureType(str, enum.Enum):
    """Digital signature types"""
    A1 = "a1"  # Certificado A1 (arquivo)
    A3 = "a3"  # Certificado A3 (token/cartão)
    CLOUD = "cloud"  # Assinatura em nuvem


class DigitalPrescription(Base):
    """Digital prescription with ICP-Brasil signature"""
    __tablename__ = "digital_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Prescription details
    prescription_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique prescription ID
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    
    # Participants
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Prescription information
    prescription_type = Column(Enum(PrescriptionType), nullable=False)
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.DRAFT)
    
    # Prescription content
    prescription_data = Column(JSON, nullable=False)  # Structured prescription data
    prescription_text = Column(Text, nullable=True)  # Human-readable prescription text
    
    # Digital signature
    signature_type = Column(Enum(SignatureType), nullable=True)
    certificate_serial = Column(String(255), nullable=True)  # Serial number of certificate
    signature_hash = Column(String(255), nullable=True)  # Hash of the signature
    signature_timestamp = Column(DateTime(timezone=True), nullable=True)  # When signed
    signature_valid_until = Column(DateTime(timezone=True), nullable=True)  # Certificate expiry
    
    # PDF generation
    pdf_path = Column(String(500), nullable=True)  # Path to generated PDF
    pdf_hash = Column(String(255), nullable=True)  # Hash of PDF content
    qr_code_url = Column(String(500), nullable=True)  # QR code for verification
    
    # Delivery information
    delivery_method = Column(String(50), nullable=True)  # email, whatsapp, portal, link
    delivery_status = Column(String(20), default="pending")  # pending, sent, delivered, failed
    delivery_timestamp = Column(DateTime(timezone=True), nullable=True)
    delivery_recipient = Column(String(255), nullable=True)  # Email or phone
    
    # Compliance and validation
    is_valid = Column(Boolean, default=True)
    validation_timestamp = Column(DateTime(timezone=True), nullable=True)
    validation_errors = Column(JSON, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    signed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant")
    appointment = relationship("Appointment")
    doctor = relationship("User", foreign_keys=[doctor_id])
    patient = relationship("Patient")
    medications = relationship("PrescriptionMedication", back_populates="prescription")
    verifications = relationship("PrescriptionVerification", back_populates="prescription")


class PrescriptionMedication(Base):
    """Medications in a prescription"""
    __tablename__ = "prescription_medications"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("digital_prescriptions.id"), nullable=False, index=True)
    
    # Medication details
    medication_name = Column(String(255), nullable=False)
    active_ingredient = Column(String(255), nullable=True)
    dosage_form = Column(String(100), nullable=True)  # tablet, capsule, syrup, etc.
    strength = Column(String(100), nullable=True)  # 500mg, 10ml, etc.
    
    # Prescription details
    dosage = Column(String(255), nullable=False)  # "1 comprimido"
    frequency = Column(String(100), nullable=False)  # "3x ao dia"
    duration = Column(String(100), nullable=False)  # "7 dias"
    route = Column(String(100), nullable=True)  # "via oral", "via intravenosa"
    instructions = Column(Text, nullable=True)  # Additional instructions
    
    # Regulatory information
    anvisa_registration = Column(String(50), nullable=True)  # ANVISA registration number
    controlled_substance = Column(Boolean, default=False)
    controlled_class = Column(String(10), nullable=True)  # C1, C2, C3, C4, C5
    
    # Quantity and refills
    quantity = Column(Integer, nullable=True)  # Number of units
    refills_allowed = Column(Integer, default=0)  # Number of refills
    
    # Order in prescription
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prescription = relationship("DigitalPrescription", back_populates="medications")


class PrescriptionVerification(Base):
    """Prescription verification records"""
    __tablename__ = "prescription_verifications"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("digital_prescriptions.id"), nullable=False, index=True)
    
    # Verification details
    verification_token = Column(String(255), unique=True, nullable=False, index=True)
    verification_url = Column(String(500), nullable=False)
    
    # Verification request
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification result
    is_valid = Column(Boolean, nullable=True)
    verification_timestamp = Column(DateTime(timezone=True), nullable=True)
    verification_details = Column(JSON, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prescription = relationship("DigitalPrescription", back_populates="verifications")


class PrescriptionConfiguration(Base):
    """Digital prescription configuration for tenants"""
    __tablename__ = "prescription_configuration"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Basic settings
    is_enabled = Column(Boolean, default=False)
    clinic_name = Column(String(255), nullable=False)
    clinic_cnpj = Column(String(18), nullable=True)
    clinic_address = Column(Text, nullable=True)
    clinic_phone = Column(String(20), nullable=True)
    clinic_email = Column(String(255), nullable=True)
    
    # Digital signature settings
    signature_enabled = Column(Boolean, default=True)
    default_signature_type = Column(Enum(SignatureType), default=SignatureType.A1)
    certificate_path = Column(String(500), nullable=True)  # Path to certificate file
    certificate_password = Column(String(255), nullable=True)  # Encrypted password
    
    # PDF settings
    pdf_template = Column(String(100), default="standard")  # Template for PDF generation
    include_clinic_logo = Column(Boolean, default=True)
    logo_path = Column(String(500), nullable=True)
    include_qr_code = Column(Boolean, default=True)
    
    # Compliance settings
    enforce_anvisa_rules = Column(Boolean, default=True)
    require_controlled_substance_justification = Column(Boolean, default=True)
    max_prescription_validity_days = Column(Integer, default=30)
    
    # Delivery settings
    default_delivery_method = Column(String(50), default="email")
    auto_send_prescription = Column(Boolean, default=False)
    send_to_patient_portal = Column(Boolean, default=True)
    
    # Notification settings
    notify_doctor_on_delivery = Column(Boolean, default=True)
    notify_patient_on_ready = Column(Boolean, default=True)
    
    # Security settings
    encrypt_prescriptions = Column(Boolean, default=True)
    audit_all_access = Column(Boolean, default=True)
    retention_days = Column(Integer, default=365)  # How long to keep prescriptions
    
    # Integration settings
    integrate_with_pharmacy = Column(Boolean, default=False)
    pharmacy_api_endpoint = Column(String(500), nullable=True)
    pharmacy_api_key = Column(String(255), nullable=True)  # Encrypted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")


class PrescriptionTemplate(Base):
    """Prescription templates for common medications"""
    __tablename__ = "prescription_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    specialty = Column(String(100), nullable=True)  # Cardiology, Neurology, etc.
    
    # Template content
    template_data = Column(JSON, nullable=False)  # Structured template data
    template_text = Column(Text, nullable=True)  # Template text
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Template metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tags = Column(JSON, nullable=True)  # Tags for categorization
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    creator = relationship("User")


class PrescriptionAnalytics(Base):
    """Analytics for prescription usage"""
    __tablename__ = "prescription_analytics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # Prescription metrics
    total_prescriptions = Column(Integer, default=0)
    signed_prescriptions = Column(Integer, default=0)
    delivered_prescriptions = Column(Integer, default=0)
    cancelled_prescriptions = Column(Integer, default=0)
    
    # Type breakdown
    common_prescriptions = Column(Integer, default=0)
    antimicrobial_prescriptions = Column(Integer, default=0)
    controlled_prescriptions = Column(Integer, default=0)
    
    # Delivery metrics
    email_deliveries = Column(Integer, default=0)
    whatsapp_deliveries = Column(Integer, default=0)
    portal_deliveries = Column(Integer, default=0)
    link_deliveries = Column(Integer, default=0)
    
    # Verification metrics
    total_verifications = Column(Integer, default=0)
    successful_verifications = Column(Integer, default=0)
    failed_verifications = Column(Integer, default=0)
    
    # Doctor metrics
    prescriptions_by_doctor = Column(JSON, nullable=True)  # Doctor ID -> count mapping
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
