from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.models.base import Base

class PrescriptionControlLevel(enum.Enum):
    A1 = "A1"  # Controlled substances - highest level
    A2 = "A2"  # Controlled substances - high level
    A3 = "A3"  # Controlled substances - medium level
    B1 = "B1"  # Controlled substances - low level
    B2 = "B2"  # Controlled substances - lowest level
    C1 = "C1"  # Prescription only
    C2 = "C2"  # Prescription only - special control
    C3 = "C3"  # Prescription only - additional control
    M1 = "M1"  # Over-the-counter
    M2 = "M2"  # Over-the-counter - restricted

class PrescriptionStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SADTType(enum.Enum):
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    SURGERY = "surgery"
    EXAMINATION = "examination"
    THERAPY = "therapy"
    EMERGENCY = "emergency"

class SADTStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class ICDCategory(enum.Enum):
    DISEASE = "disease"
    INJURY = "injury"
    EXTERNAL_CAUSE = "external_cause"
    PROCEDURE = "procedure"
    SYMPTOM = "symptom"
    SIGN = "sign"

class ControlledPrescription(Base):
    """Controlled prescription management with regulatory compliance"""
    __tablename__ = "controlled_prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_number = Column(String(50), unique=True, nullable=False)
    
    # Patient and Doctor Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prescription Details
    medication_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=True)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Control Information
    control_level = Column(Enum(PrescriptionControlLevel), nullable=False)
    anvisa_code = Column(String(50), nullable=True)  # ANVISA registration code
    controlled_substance = Column(Boolean, default=False)
    requires_special_authorization = Column(Boolean, default=False)
    
    # Regulatory Information
    prescription_date = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    refills_allowed = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    
    # Status and Tracking
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.DRAFT)
    dispensed = Column(Boolean, default=False)
    dispensed_at = Column(DateTime(timezone=True), nullable=True)
    dispensed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Digital Signature and Compliance
    digital_signature = Column(Text, nullable=True)
    prescription_hash = Column(String(256), nullable=True)  # For integrity verification
    regulatory_compliance = Column(JSON, nullable=True)  # Compliance tracking
    
    # Additional Information
    instructions = Column(Text, nullable=True)
    side_effects = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    interactions = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    dispenser = relationship("User", foreign_keys=[dispensed_by])
    creator = relationship("User", foreign_keys=[created_by])
    refills = relationship("PrescriptionRefill", back_populates="prescription")

class PrescriptionRefill(Base):
    """Prescription refill tracking"""
    __tablename__ = "prescription_refills"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("controlled_prescriptions.id"), nullable=False)
    
    # Refill Details
    refill_number = Column(Integer, nullable=False)
    refill_date = Column(DateTime(timezone=True), nullable=False)
    quantity_dispensed = Column(Integer, nullable=False)
    
    # Dispensing Information
    dispensed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    pharmacy_name = Column(String(200), nullable=True)
    pharmacy_address = Column(Text, nullable=True)
    
    # Compliance
    patient_identification_verified = Column(Boolean, default=False)
    prescription_verified = Column(Boolean, default=False)
    regulatory_compliance_checked = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prescription = relationship("ControlledPrescription", back_populates="refills")
    dispenser = relationship("User")

class SADT(Base):
    """SADT (Solicitação de Autorização de Procedimentos) - Procedure Authorization Request"""
    __tablename__ = "sadt"
    
    id = Column(Integer, primary_key=True, index=True)
    sadt_number = Column(String(50), unique=True, nullable=False)
    
    # Patient and Doctor Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # SADT Details
    sadt_type = Column(Enum(SADTType), nullable=False)
    procedure_name = Column(String(200), nullable=False)
    procedure_code = Column(String(50), nullable=True)  # TUSS code
    description = Column(Text, nullable=False)
    
    # Medical Justification
    clinical_indication = Column(Text, nullable=False)
    medical_history = Column(Text, nullable=True)
    current_symptoms = Column(Text, nullable=True)
    physical_examination = Column(Text, nullable=True)
    diagnostic_hypothesis = Column(Text, nullable=False)
    
    # Authorization Information
    requested_date = Column(DateTime(timezone=True), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    authorized_date = Column(DateTime(timezone=True), nullable=True)
    authorized_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    authorization_number = Column(String(50), nullable=True)
    
    # Status and Tracking
    status = Column(Enum(SADTStatus), default=SADTStatus.SCHEDULED)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    
    # Health Plan Information
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=True)
    health_plan_authorization = Column(String(50), nullable=True)
    copayment_required = Column(Boolean, default=False)
    copayment_amount = Column(Numeric(10, 2), nullable=True)
    
    # Results and Follow-up
    procedure_results = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    
    # Compliance and Documentation
    regulatory_compliance = Column(JSON, nullable=True)
    required_documents = Column(JSON, nullable=True)
    attached_documents = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    authorizer = relationship("User", foreign_keys=[authorized_by])
    creator = relationship("User", foreign_keys=[created_by])
    health_plan = relationship("HealthPlan")
    icd_codes = relationship("SADTICDCode", back_populates="sadt")

class SADTICDCode(Base):
    """ICD codes associated with SADT procedures"""
    __tablename__ = "sadt_icd_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    sadt_id = Column(Integer, ForeignKey("sadt.id"), nullable=False)
    
    # ICD Code Information
    icd_code = Column(String(20), nullable=False)
    icd_category = Column(Enum(ICDCategory), nullable=False)
    icd_description = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary diagnosis
    
    # Additional Information
    severity = Column(String(50), nullable=True)
    laterality = Column(String(50), nullable=True)  # Left, Right, Bilateral
    episode_type = Column(String(50), nullable=True)  # Initial, Subsequent, Sequela
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sadt = relationship("SADT", back_populates="icd_codes")

class ICDCode(Base):
    """ICD-10 code database"""
    __tablename__ = "icd_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(Enum(ICDCategory), nullable=False)
    
    # Additional Information
    parent_code = Column(String(20), nullable=True)
    is_leaf = Column(Boolean, default=True)  # Leaf node in hierarchy
    level = Column(Integer, default=1)  # Hierarchy level
    
    # Brazilian Specific
    cid10_code = Column(String(20), nullable=True)  # Brazilian CID-10 code
    cid10_description = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("ICDCode", remote_side=[id], backref="children")

class MedicalProcedure(Base):
    """Medical procedures with TUSS codes"""
    __tablename__ = "medical_procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    tuss_code = Column(String(50), unique=True, nullable=False)
    procedure_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    procedure_type = Column(Enum(SADTType), nullable=False)
    specialty = Column(String(100), nullable=True)
    complexity = Column(String(50), nullable=True)  # Simple, Medium, Complex
    
    # Financial Information
    base_value = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="BRL")
    
    # Regulatory Information
    anvisa_authorization = Column(Boolean, default=False)
    cff_authorization = Column(Boolean, default=False)  # Conselho Federal de Farmácia
    crm_authorization = Column(Boolean, default=False)  # Conselho Regional de Medicina
    
    # Requirements
    minimum_qualification = Column(String(100), nullable=True)
    required_equipment = Column(JSON, nullable=True)
    contraindications = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sadt_requests = relationship("SADT")

class HealthPlan(Base):
    """Health plan information for SADT authorization"""
    __tablename__ = "health_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String(200), nullable=False)
    plan_code = Column(String(50), unique=True, nullable=False)
    
    # Plan Details
    plan_type = Column(String(100), nullable=False)  # Individual, Family, Corporate
    coverage_type = Column(String(100), nullable=False)  # Basic, Standard, Premium
    
    # Authorization Process
    requires_authorization = Column(Boolean, default=True)
    authorization_timeframe = Column(Integer, nullable=True)  # in hours
    emergency_authorization = Column(Boolean, default=False)
    
    # Financial Information
    copayment_required = Column(Boolean, default=False)
    copayment_percentage = Column(Float, nullable=True)
    annual_limit = Column(Numeric(10, 2), nullable=True)
    procedure_limit = Column(Numeric(10, 2), nullable=True)
    
    # Contact Information
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sadt_requests = relationship("SADT")

class PrescriptionAudit(Base):
    """Audit trail for controlled prescriptions"""
    __tablename__ = "prescription_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("controlled_prescriptions.id"), nullable=False)
    
    # Audit Information
    action = Column(String(50), nullable=False)  # created, updated, dispensed, cancelled
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    
    # User Information
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional Details
    reason = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prescription = relationship("ControlledPrescription")
    user = relationship("User")

class SADTAudit(Base):
    """Audit trail for SADT requests"""
    __tablename__ = "sadt_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    sadt_id = Column(Integer, ForeignKey("sadt.id"), nullable=False)
    
    # Audit Information
    action = Column(String(50), nullable=False)  # created, updated, authorized, cancelled
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    
    # User Information
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional Details
    reason = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sadt = relationship("SADT")
    user = relationship("User")
