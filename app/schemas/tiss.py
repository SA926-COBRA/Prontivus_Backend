"""
TISS Integration Schemas
Pydantic schemas for TISS integration API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EnvironmentEnum(str, Enum):
    HOMOLOGATION = "homologation"
    PRODUCTION = "production"


class TransactionTypeEnum(str, Enum):
    AUTHORIZATION = "authorization"
    BILLING = "billing"
    SADT = "sadt"
    PRESCRIPTION = "prescription"


class TransactionStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


# Base schemas
class TISSInsuranceOperatorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    cnpj: Optional[str] = Field(None, max_length=18)
    is_active: bool = True


class TISSInsuranceOperatorCreate(TISSInsuranceOperatorBase):
    pass


class TISSInsuranceOperatorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    cnpj: Optional[str] = Field(None, max_length=18)
    is_active: Optional[bool] = None


class TISSInsuranceOperator(TISSInsuranceOperatorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Credentials schemas
class TISSCredentialsBase(BaseModel):
    operator_id: int
    environment: EnvironmentEnum = EnvironmentEnum.HOMOLOGATION
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    token: Optional[str] = None
    homologation_url: Optional[str] = Field(None, max_length=500)
    production_url: Optional[str] = Field(None, max_length=500)
    requires_doctor_identification: bool = True
    additional_config: Optional[Dict[str, Any]] = None


class TISSCredentialsCreate(TISSCredentialsBase):
    pass


class TISSCredentialsUpdate(BaseModel):
    environment: Optional[EnvironmentEnum] = None
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=1)
    token: Optional[str] = None
    homologation_url: Optional[str] = Field(None, max_length=500)
    production_url: Optional[str] = Field(None, max_length=500)
    requires_doctor_identification: Optional[bool] = None
    additional_config: Optional[Dict[str, Any]] = None


class TISSCredentials(TISSCredentialsBase):
    id: int
    tenant_id: int
    is_active: bool
    last_connection_success: Optional[datetime] = None
    last_connection_error: Optional[str] = None
    connection_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TISSCredentialsTest(BaseModel):
    """Schema for testing TISS credentials"""
    credentials_id: int


class TISSCredentialsTestResponse(BaseModel):
    success: bool
    message: str
    connection_time: Optional[float] = None
    response_data: Optional[Dict[str, Any]] = None


# Doctor codes schemas
class TISSDoctorCodeBase(BaseModel):
    doctor_id: int
    operator_id: int
    doctor_code: str = Field(..., min_length=1, max_length=100)
    crm: Optional[str] = Field(None, max_length=20)
    cpf: Optional[str] = Field(None, max_length=14)
    specialty_code: Optional[str] = Field(None, max_length=50)
    additional_info: Optional[Dict[str, Any]] = None


class TISSDoctorCodeCreate(TISSDoctorCodeBase):
    pass


class TISSDoctorCodeUpdate(BaseModel):
    doctor_code: Optional[str] = Field(None, min_length=1, max_length=100)
    crm: Optional[str] = Field(None, max_length=20)
    cpf: Optional[str] = Field(None, max_length=14)
    specialty_code: Optional[str] = Field(None, max_length=50)
    additional_info: Optional[Dict[str, Any]] = None


class TISSDoctorCode(TISSDoctorCodeBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Transaction schemas
class TISSTransactionBase(BaseModel):
    operator_id: int
    doctor_id: int
    transaction_type: TransactionTypeEnum
    transaction_id: str = Field(..., min_length=1, max_length=100)
    patient_id: Optional[int] = None
    request_data: Optional[Dict[str, Any]] = None


class TISSTransactionCreate(TISSTransactionBase):
    pass


class TISSTransactionUpdate(BaseModel):
    response_data: Optional[Dict[str, Any]] = None
    status: Optional[TransactionStatusEnum] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None


class TISSTransaction(TISSTransactionBase):
    id: int
    tenant_id: int
    response_data: Optional[Dict[str, Any]] = None
    status: TransactionStatusEnum
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Configuration schemas
class TISSConfigurationBase(BaseModel):
    is_enabled: bool = False
    default_environment: EnvironmentEnum = EnvironmentEnum.HOMOLOGATION
    sadt_enabled: bool = True
    sadt_auto_generate: bool = False
    billing_enabled: bool = True
    auto_billing: bool = False
    notify_on_error: bool = True
    notify_email: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class TISSConfigurationCreate(TISSConfigurationBase):
    pass


class TISSConfigurationUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    default_environment: Optional[EnvironmentEnum] = None
    sadt_enabled: Optional[bool] = None
    sadt_auto_generate: Optional[bool] = None
    billing_enabled: Optional[bool] = None
    auto_billing: Optional[bool] = None
    notify_on_error: Optional[bool] = None
    notify_email: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class TISSConfiguration(TISSConfigurationBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Response schemas
class TISSDashboardResponse(BaseModel):
    """Dashboard response with summary data"""
    total_operators: int
    active_operators: int
    total_credentials: int
    active_credentials: int
    recent_transactions: int
    success_rate: float
    last_connection_status: Dict[str, Any]


class TISSOperatorStatus(BaseModel):
    """Status of TISS operator connection"""
    operator_id: int
    operator_name: str
    environment: str
    connection_status: str
    last_connection_success: Optional[datetime] = None
    last_connection_error: Optional[str] = None
    is_active: bool


class TISSOperatorsStatusResponse(BaseModel):
    """Response with status of all operators"""
    operators: List[TISSOperatorStatus]
    total_operators: int
    active_operators: int
    error_operators: int
