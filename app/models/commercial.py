from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.database import Base

class ProcedureType(enum.Enum):
    SURGICAL = "surgical"
    DIAGNOSTIC = "diagnostic"
    THERAPEUTIC = "therapeutic"
    COSMETIC = "cosmetic"
    EMERGENCY = "emergency"

class EstimateStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class ContractStatus(enum.Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class SurgicalProcedure(Base):
    """Surgical procedures catalog"""
    __tablename__ = "surgical_procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    procedure_type = Column(Enum(ProcedureType), nullable=False)
    category = Column(String(100))  # e.g., "Cardiology", "Orthopedics"
    specialty = Column(String(100))  # Medical specialty
    
    # Pricing
    base_price = Column(Float, nullable=False)
    min_price = Column(Float)
    max_price = Column(Float)
    currency = Column(String(3), default="BRL")
    
    # Procedure details
    duration_minutes = Column(Integer)  # Estimated duration
    complexity_level = Column(Integer)  # 1-5 scale
    requires_anesthesia = Column(Boolean, default=False)
    requires_hospitalization = Column(Boolean, default=False)
    recovery_days = Column(Integer)
    
    # Requirements
    required_equipment = Column(JSON)  # List of required equipment
    required_supplies = Column(JSON)   # List of required supplies
    prerequisites = Column(Text)       # Medical prerequisites
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    estimates = relationship("SurgicalEstimate", back_populates="procedure")
    contracts = relationship("SurgicalContract", back_populates="procedure")

class SurgicalEstimate(Base):
    """Surgical procedure estimates for patients"""
    __tablename__ = "surgical_estimates"
    
    id = Column(Integer, primary_key=True, index=True)
    estimate_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Patient and procedure
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    procedure_id = Column(Integer, ForeignKey("surgical_procedures.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Estimate details
    status = Column(Enum(EstimateStatus), default=EstimateStatus.DRAFT)
    estimated_date = Column(DateTime(timezone=True))
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Pricing breakdown
    base_price = Column(Float, nullable=False)
    additional_fees = Column(Float, default=0)  # Anesthesia, materials, etc.
    discount_percentage = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total_price = Column(Float, nullable=False)
    
    # Payment terms
    payment_terms = Column(String(100))  # e.g., "30 days", "Cash", "Installments"
    installment_count = Column(Integer, default=1)
    installment_value = Column(Float)
    
    # Insurance and coverage
    insurance_covered = Column(Boolean, default=False)
    insurance_company = Column(String(200))
    insurance_authorization = Column(String(100))
    copay_amount = Column(Float, default=0)
    
    # Additional information
    notes = Column(Text)
    special_requirements = Column(Text)
    contraindications = Column(Text)
    
    # Validity
    valid_until = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient", back_populates="surgical_estimates")
    procedure = relationship("SurgicalProcedure", back_populates="estimates")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])
    contracts = relationship("SurgicalContract", back_populates="estimate")

class SurgicalContract(Base):
    """Surgical procedure contracts"""
    __tablename__ = "surgical_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Related entities
    estimate_id = Column(Integer, ForeignKey("surgical_estimates.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    procedure_id = Column(Integer, ForeignKey("surgical_procedures.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contract details
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    contract_type = Column(String(50), default="standard")  # standard, emergency, package
    
    # Financial terms
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)
    remaining_amount = Column(Float, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Payment schedule
    payment_schedule = Column(JSON)  # List of payment installments
    due_dates = Column(JSON)         # Payment due dates
    
    # Contract terms
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    procedure_date = Column(DateTime(timezone=True))
    
    # Legal and compliance
    terms_and_conditions = Column(Text)
    cancellation_policy = Column(Text)
    warranty_period_days = Column(Integer, default=30)
    
    # Signatures and approvals
    patient_signed = Column(Boolean, default=False)
    patient_signature_date = Column(DateTime(timezone=True))
    doctor_approved = Column(Boolean, default=False)
    doctor_approval_date = Column(DateTime(timezone=True))
    admin_approved = Column(Boolean, default=False)
    admin_approval_date = Column(DateTime(timezone=True))
    
    # Additional information
    special_conditions = Column(Text)
    risk_assessment = Column(Text)
    post_procedure_care = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    estimate = relationship("SurgicalEstimate", back_populates="contracts")
    patient = relationship("Patient", back_populates="surgical_contracts")
    procedure = relationship("SurgicalProcedure", back_populates="contracts")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])
    payments = relationship("ContractPayment", back_populates="contract")

class ContractPayment(Base):
    """Payment records for surgical contracts"""
    __tablename__ = "contract_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("surgical_contracts.id"), nullable=False)
    
    # Payment details
    payment_number = Column(String(50), unique=True, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))  # cash, card, transfer, check
    payment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Payment status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    processed_by = Column(Integer, ForeignKey("users.id"))
    
    # Additional information
    reference_number = Column(String(100))  # Bank reference, transaction ID
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contract = relationship("SurgicalContract", back_populates="payments")
    processor = relationship("User", foreign_keys=[processed_by])

class CommercialPackage(Base):
    """Commercial packages for multiple procedures"""
    __tablename__ = "commercial_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    package_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Package details
    procedures = Column(JSON)  # List of procedure IDs and quantities
    total_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0)
    final_price = Column(Float, nullable=False)
    
    # Validity and availability
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    max_uses = Column(Integer)  # Maximum number of times this package can be sold
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class SalesTarget(Base):
    """Sales targets for commercial team"""
    __tablename__ = "sales_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Target details
    target_period = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    target_year = Column(Integer, nullable=False)
    target_month = Column(Integer)  # For monthly targets
    target_quarter = Column(Integer)  # For quarterly targets
    
    # Target metrics
    revenue_target = Column(Float, nullable=False)
    procedure_count_target = Column(Integer, nullable=False)
    contract_count_target = Column(Integer, nullable=False)
    
    # Assignee
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Progress tracking
    current_revenue = Column(Float, default=0)
    current_procedures = Column(Integer, default=0)
    current_contracts = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
