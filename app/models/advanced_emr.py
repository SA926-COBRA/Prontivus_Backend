"""
Advanced Electronic Medical Records (EMR) Models
Supports controlled prescriptions, SADT, ICD-10 integration
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid
from datetime import datetime


class ICD10Code(Base):
    """ICD-10 International Classification of Diseases codes"""
    __tablename__ = "icd10_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientHistory(Base):
    """Comprehensive patient medical history"""
    __tablename__ = "patient_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_type = Column(String(50))  # consultation, follow_up, emergency, etc.
    
    # Chief Complaint
    chief_complaint = Column(Text)
    present_illness = Column(Text)
    
    # Medical History
    past_medical_history = Column(Text)
    family_history = Column(Text)
    social_history = Column(Text)
    allergies = Column(Text)
    current_medications = Column(Text)
    
    # Physical Examination
    vital_signs = Column(JSON)  # BP, HR, Temp, etc.
    physical_exam = Column(Text)
    systems_review = Column(Text)
    
    # Assessment & Plan
    assessment = Column(Text)
    plan = Column(Text)
    follow_up_instructions = Column(Text)
    
    # ICD-10 Integration
    primary_diagnosis_code = Column(String(10), ForeignKey("icd10_codes.code"))
    secondary_diagnosis_codes = Column(JSON)  # Array of ICD-10 codes
    
    # SADT Integration
    exam_requests = Column(JSON)  # Requested exams/procedures
    procedure_codes = Column(JSON)  # SADT procedure codes
    
    # Attachments
    attachments = Column(JSON)  # File references
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_histories")
    doctor = relationship("User", foreign_keys=[doctor_id])
    primary_diagnosis = relationship("ICD10Code", foreign_keys=[primary_diagnosis_code])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class PrescriptionType(Base):
    """Prescription types: regular, antimicrobial, C1"""
    __tablename__ = "prescription_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # REG, ANT, C1
    description = Column(Text)
    requires_special_approval = Column(Boolean, default=False)
    max_copies = Column(Integer, default=1)  # C1 prescriptions require 2 copies
    is_active = Column(Boolean, default=True)


class Prescription(Base):
    """Advanced prescription with ICP-Brasil signature support"""
    __tablename__ = "advanced_prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_number = Column(String(50), unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prescription_type_id = Column(Integer, ForeignKey("prescription_types.id"), nullable=False)
    
    # Prescription Details
    issue_date = Column(Date, nullable=False)
    valid_until = Column(Date)
    
    # Patient Information
    patient_name = Column(String(200), nullable=False)
    patient_cpf = Column(String(14))
    patient_dob = Column(Date)
    
    # Doctor Information
    doctor_name = Column(String(200), nullable=False)
    doctor_crm = Column(String(20), nullable=False)
    doctor_crm_state = Column(String(2), nullable=False)
    clinic_name = Column(String(200))
    clinic_address = Column(Text)
    clinic_phone = Column(String(20))
    
    # Prescription Content
    medications = Column(JSON, nullable=False)  # Array of medication objects
    instructions = Column(Text)
    observations = Column(Text)
    
    # ICP-Brasil Digital Signature
    is_digitally_signed = Column(Boolean, default=False)
    certificate_serial = Column(String(200))
    signature_timestamp = Column(DateTime)
    signature_hash = Column(String(500))
    signature_valid = Column(Boolean, default=False)
    
    # QR Code Verification
    qr_code_data = Column(String(500))
    verification_url = Column(String(500))
    
    # PDF Generation
    pdf_path = Column(String(500))
    pdf_generated_at = Column(DateTime)
    
    # Status
    status = Column(String(20), default="draft")  # draft, signed, delivered, verified
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", foreign_keys=[doctor_id])
    prescription_type = relationship("PrescriptionType")


class PrescriptionMedication(Base):
    """Individual medications within a prescription"""
    __tablename__ = "advanced_prescription_medications"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("advanced_prescriptions.id"), nullable=False)
    
    # Medication Details
    medication_name = Column(String(200), nullable=False)
    active_ingredient = Column(String(200))
    concentration = Column(String(100))  # e.g., "500mg", "10ml"
    pharmaceutical_form = Column(String(100))  # tablet, syrup, injection, etc.
    
    # Dosage
    dosage = Column(String(100), nullable=False)  # e.g., "1 tablet", "2ml"
    frequency = Column(String(100), nullable=False)  # e.g., "3x daily", "every 8 hours"
    duration = Column(String(100))  # e.g., "7 days", "until finished"
    total_quantity = Column(String(100))  # e.g., "21 tablets", "100ml"
    
    # Special Instructions
    administration_route = Column(String(100))  # oral, topical, injection, etc.
    special_instructions = Column(Text)
    
    # Regulatory Information
    requires_prescription = Column(Boolean, default=True)
    controlled_substance = Column(Boolean, default=False)
    antimicrobial = Column(Boolean, default=False)
    
    # Relationships
    prescription = relationship("Prescription", back_populates="medications")


class SADTRequest(Base):
    """SADT (Serviços Auxiliares de Diagnóstico e Terapia) requests"""
    __tablename__ = "sadt_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(50), unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medical_history_id = Column(Integer, ForeignKey("patient_histories.id"))
    
    # Request Details
    request_date = Column(Date, nullable=False)
    service_type = Column(String(50), nullable=False)  # exam, procedure, therapy
    service_category = Column(String(100))  # laboratory, imaging, therapy, etc.
    
    # Service Information
    service_name = Column(String(200), nullable=False)
    service_code = Column(String(50))  # TISS procedure code
    service_description = Column(Text)
    
    # Clinical Information
    clinical_indication = Column(Text, nullable=False)
    clinical_question = Column(Text)
    urgency_level = Column(String(20), default="routine")  # emergency, urgent, routine
    
    # Insurance Information
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))
    authorization_number = Column(String(100))
    authorization_status = Column(String(20))  # pending, approved, denied
    
    # Status
    status = Column(String(20), default="draft")  # draft, submitted, approved, completed, cancelled
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    medical_history = relationship("PatientHistory")
    health_plan = relationship("HealthPlan")


class PrescriptionAuditLog(Base):
    """Audit log for prescription activities"""
    __tablename__ = "prescription_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("advanced_prescriptions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Action Details
    action = Column(String(50), nullable=False)  # created, modified, signed, verified, etc.
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prescription = relationship("Prescription")
    user = relationship("User")


# Update existing Patient model relationships
# Patient model is defined in patient.py - we don't redefine it here
# The relationships with Patient are handled through foreign keys in other models


# User model is defined in user.py - we don't redefine it here
# The relationships with User are handled through foreign keys in other models