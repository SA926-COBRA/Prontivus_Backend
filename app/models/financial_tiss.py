from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

from app.database.database import Base

class TISSCategory(enum.Enum):
    MEDICAL_CONSULTATION = "medical_consultation"
    SURGICAL_PROCEDURE = "surgical_procedure"
    DIAGNOSTIC_EXAM = "diagnostic_exam"
    THERAPEUTIC_PROCEDURE = "therapeutic_procedure"
    EMERGENCY_CARE = "emergency_care"
    HOSPITALIZATION = "hospitalization"
    OUTPATIENT_CARE = "outpatient_care"

class TISSStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PAID = "paid"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class TISSCode(Base):
    """TISS (Terminologia Unificada da Saúde Suplementar) codes database"""
    __tablename__ = "tiss_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(500), nullable=False)
    category = Column(Enum(TISSCategory), nullable=False)
    
    # Financial Information
    base_value = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="BRL")
    unit_of_measure = Column(String(50), nullable=True)  # unit, hour, session, etc.
    
    # Regulatory Information
    anvisa_authorization = Column(Boolean, default=False)
    cff_authorization = Column(Boolean, default=False)  # Conselho Federal de Farmácia
    crm_authorization = Column(Boolean, default=False)  # Conselho Regional de Medicina
    
    # TISS Specific
    tiss_version = Column(String(10), nullable=False)  # TISS version
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    
    # Additional Information
    requirements = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    procedures = relationship("TISSProcedure", back_populates="tiss_code")

class TISSProcedure(Base):
    """TISS procedures performed on patients"""
    __tablename__ = "tiss_procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    procedure_number = Column(String(50), unique=True, nullable=False)
    
    # Patient and Doctor Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # TISS Information
    tiss_code_id = Column(Integer, ForeignKey("tiss_codes.id"), nullable=False)
    procedure_date = Column(DateTime(timezone=True), nullable=False)
    procedure_time = Column(Integer, nullable=True)  # duration in minutes
    
    # Medical Information
    medical_indication = Column(Text, nullable=False)
    procedure_description = Column(Text, nullable=True)
    results = Column(Text, nullable=True)
    complications = Column(Text, nullable=True)
    
    # Financial Information
    base_value = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, default=0.0)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    final_value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Health Plan Information
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=True)
    authorization_number = Column(String(50), nullable=True)
    copayment_required = Column(Boolean, default=False)
    copayment_amount = Column(Numeric(10, 2), nullable=True)
    
    # Status and Tracking
    status = Column(Enum(TISSStatus), default=TISSStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # TISS Integration
    tiss_submission_id = Column(String(100), nullable=True)
    tiss_response = Column(JSON, nullable=True)
    tiss_errors = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    creator = relationship("User", foreign_keys=[created_by])
    tiss_code = relationship("TISSCode", back_populates="procedures")
    health_plan = relationship("HealthPlan")
    invoices = relationship("Invoice", back_populates="procedure")

class Invoice(Base):
    """Financial invoices for TISS procedures"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    
    # Related Information
    procedure_id = Column(Integer, ForeignKey("tiss_procedures.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=True)
    
    # Invoice Details
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    
    # Financial Information
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    tax_amount = Column(Numeric(10, 2), default=0.0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.0)
    currency = Column(String(3), default="BRL")
    
    # Status
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    procedure = relationship("TISSProcedure", back_populates="invoices")
    patient = relationship("Patient")
    health_plan = relationship("HealthPlan")
    creator = relationship("User", foreign_keys=[created_by])
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    """Payment records for invoices"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False)
    
    # Related Information
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Payment Details
    payment_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Payment Method
    payment_method = Column(String(50), nullable=False)  # cash, card, transfer, etc.
    payment_reference = Column(String(100), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("Patient")
    processor = relationship("User", foreign_keys=[processed_by])
    creator = relationship("User", foreign_keys=[created_by])

class FinancialReport(Base):
    """Financial reports and analytics"""
    __tablename__ = "financial_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    
    # Report Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Financial Summary
    total_procedures = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=0.0)
    total_payments = Column(Numeric(12, 2), default=0.0)
    total_outstanding = Column(Numeric(12, 2), default=0.0)
    
    # Breakdown by Category
    revenue_by_category = Column(JSON, nullable=True)
    payments_by_method = Column(JSON, nullable=True)
    outstanding_by_health_plan = Column(JSON, nullable=True)
    
    # Report Data
    report_data = Column(JSON, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class TISSIntegration(Base):
    """TISS integration configuration and logs"""
    __tablename__ = "tiss_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_name = Column(String(100), nullable=False)
    
    # Configuration
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=False)
    api_endpoint = Column(String(500), nullable=False)
    api_key = Column(String(200), nullable=True)
    api_secret = Column(String(200), nullable=True)
    
    # TISS Settings
    tiss_version = Column(String(10), nullable=False)
    submission_frequency = Column(String(20), default="daily")  # daily, weekly, monthly
    auto_submission = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_plan = relationship("HealthPlan")
    creator = relationship("User", foreign_keys=[created_by])
    submissions = relationship("TISSSubmission", back_populates="integration")

class TISSSubmission(Base):
    """TISS submission logs and status"""
    __tablename__ = "tiss_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, nullable=False)
    
    # Related Information
    integration_id = Column(Integer, ForeignKey("tiss_integrations.id"), nullable=False)
    procedure_id = Column(Integer, ForeignKey("tiss_procedures.id"), nullable=True)
    
    # Submission Details
    submission_date = Column(DateTime(timezone=True), nullable=False)
    submission_type = Column(String(50), nullable=False)  # procedure, batch, etc.
    
    # TISS Data
    tiss_xml = Column(Text, nullable=True)
    tiss_response = Column(Text, nullable=True)
    tiss_status = Column(String(50), nullable=True)
    tiss_message = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(TISSStatus), default=TISSStatus.PENDING)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    integration = relationship("TISSIntegration", back_populates="submissions")
    procedure = relationship("TISSProcedure")

class HealthPlanFinancial(Base):
    """Health plan financial information and contracts"""
    __tablename__ = "health_plan_financials"
    
    id = Column(Integer, primary_key=True, index=True)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=False)
    
    # Contract Information
    contract_number = Column(String(100), nullable=True)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date, nullable=True)
    
    # Financial Terms
    payment_terms = Column(String(100), nullable=True)  # 30 days, 60 days, etc.
    discount_percentage = Column(Float, default=0.0)
    copayment_percentage = Column(Float, default=0.0)
    
    # Limits and Caps
    annual_limit = Column(Numeric(12, 2), nullable=True)
    procedure_limit = Column(Numeric(10, 2), nullable=True)
    monthly_cap = Column(Numeric(12, 2), nullable=True)
    
    # Current Status
    current_balance = Column(Numeric(12, 2), default=0.0)
    outstanding_amount = Column(Numeric(12, 2), default=0.0)
    last_payment_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_plan = relationship("HealthPlan")
    creator = relationship("User", foreign_keys=[created_by])
