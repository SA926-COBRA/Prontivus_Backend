"""
TISS Integration Models
Models for managing TISS (Troca de Informação em Saúde Suplementar) integration
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class TISSInsuranceOperator(Base):
    """Health insurance operators for TISS integration"""
    __tablename__ = "tiss_insurance_operators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    cnpj = Column(String(18), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    credentials = relationship("TISSCredentials", back_populates="operator")
    doctor_codes = relationship("TISSDoctorCode", back_populates="operator")


class TISSCredentials(Base):
    """TISS credentials for each clinic per insurance operator"""
    __tablename__ = "tiss_credentials"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("tiss_insurance_operators.id"), nullable=False, index=True)
    
    # Environment (homologation/production)
    environment = Column(String(20), nullable=False, default="homologation")  # homologation, production
    
    # Credentials (encrypted)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)  # Encrypted
    token = Column(Text, nullable=True)  # Encrypted
    
    # Endpoints
    homologation_url = Column(String(500), nullable=True)
    production_url = Column(String(500), nullable=True)
    
    # Additional configuration
    requires_doctor_identification = Column(Boolean, default=True)
    additional_config = Column(JSON, nullable=True)  # For operator-specific settings
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    last_connection_success = Column(DateTime(timezone=True), nullable=True)
    last_connection_error = Column(Text, nullable=True)
    connection_status = Column(String(20), default="unknown")  # unknown, success, error
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="tiss_credentials")
    operator = relationship("TISSInsuranceOperator", back_populates="credentials")


class TISSDoctorCode(Base):
    """Doctor codes for each insurance operator"""
    __tablename__ = "tiss_doctor_codes"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("tiss_insurance_operators.id"), nullable=False, index=True)
    
    # Doctor identification codes
    doctor_code = Column(String(100), nullable=False)  # Código do médico na operadora
    crm = Column(String(20), nullable=True)  # CRM do médico
    cpf = Column(String(14), nullable=True)  # CPF do médico
    
    # Additional information
    specialty_code = Column(String(50), nullable=True)  # Código da especialidade
    additional_info = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    doctor = relationship("User")
    operator = relationship("TISSInsuranceOperator", back_populates="doctor_codes")


class TISSTransaction(Base):
    """TISS transaction logs"""
    __tablename__ = "tiss_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("tiss_insurance_operators.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # authorization, billing, etc.
    transaction_id = Column(String(100), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    
    # Request/Response data
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False)  # pending, success, error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    operator = relationship("TISSInsuranceOperator")
    doctor = relationship("User")
    patient = relationship("Patient")


class TISSConfiguration(Base):
    """Global TISS configuration settings"""
    __tablename__ = "tiss_configuration"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Global settings
    is_enabled = Column(Boolean, default=False)
    default_environment = Column(String(20), default="homologation")
    
    # SADT settings
    sadt_enabled = Column(Boolean, default=True)
    sadt_auto_generate = Column(Boolean, default=False)
    
    # Billing settings
    billing_enabled = Column(Boolean, default=True)
    auto_billing = Column(Boolean, default=False)
    
    # Notification settings
    notify_on_error = Column(Boolean, default=True)
    notify_email = Column(String(255), nullable=True)
    
    # Additional configuration
    settings = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
