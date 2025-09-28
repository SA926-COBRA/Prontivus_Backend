"""
TISS Integration API Endpoints
API endpoints for TISS (Troca de Informação em Saúde Suplementar) integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.services.tiss_service import TISSService
from app.schemas.tiss import (
    TISSInsuranceOperator, TISSInsuranceOperatorCreate, TISSInsuranceOperatorUpdate,
    TISSCredentials, TISSCredentialsCreate, TISSCredentialsUpdate, TISSCredentialsTestResponse,
    TISSDoctorCode, TISSDoctorCodeCreate, TISSDoctorCodeUpdate,
    TISSTransaction, TISSTransactionCreate, TISSTransactionUpdate,
    TISSConfiguration, TISSConfigurationCreate, TISSConfigurationUpdate,
    TISSDashboardResponse, TISSOperatorsStatusResponse
)
from app.core.auth import get_current_user

router = APIRouter()


def get_tiss_service(db: Session = Depends(get_db)) -> TISSService:
    """Get TISS service instance"""
    return TISSService(db)


def get_tenant_id(request: Request) -> int:
    """Extract tenant ID from request (simplified for now)"""
    # In a real implementation, this would come from JWT token or request context
    return 1  # Default tenant ID


# Insurance Operators Endpoints
@router.get("/operators", response_model=List[TISSInsuranceOperator])
async def get_insurance_operators(
    active_only: bool = True,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get all insurance operators"""
    try:
        operators = tiss_service.get_insurance_operators(active_only=active_only)
        return operators
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insurance operators: {str(e)}"
        )


@router.post("/operators", response_model=TISSInsuranceOperator, status_code=status.HTTP_201_CREATED)
async def create_insurance_operator(
    operator_data: TISSInsuranceOperatorCreate,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Create a new insurance operator"""
    try:
        operator = tiss_service.create_insurance_operator(operator_data.dict())
        return operator
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create insurance operator: {str(e)}"
        )


@router.get("/operators/{operator_id}", response_model=TISSInsuranceOperator)
async def get_insurance_operator(
    operator_id: int,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get insurance operator by ID"""
    operator = tiss_service.get_insurance_operator(operator_id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance operator not found"
        )
    return operator


@router.put("/operators/{operator_id}", response_model=TISSInsuranceOperator)
async def update_insurance_operator(
    operator_id: int,
    operator_data: TISSInsuranceOperatorUpdate,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Update insurance operator"""
    operator = tiss_service.update_insurance_operator(operator_id, operator_data.dict(exclude_unset=True))
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance operator not found"
        )
    return operator


# Credentials Endpoints
@router.get("/credentials", response_model=List[TISSCredentials])
async def get_credentials(
    operator_id: Optional[int] = None,
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get TISS credentials for the current tenant"""
    try:
        tenant_id = get_tenant_id(request)
        credentials = tiss_service.get_credentials(tenant_id, operator_id)
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials: {str(e)}"
        )


@router.post("/credentials", response_model=TISSCredentials, status_code=status.HTTP_201_CREATED)
async def create_credentials(
    credentials_data: TISSCredentialsCreate,
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Create TISS credentials"""
    try:
        tenant_id = get_tenant_id(request)
        credentials = tiss_service.create_credentials(tenant_id, credentials_data)
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credentials: {str(e)}"
        )


@router.get("/credentials/{credentials_id}", response_model=TISSCredentials)
async def get_credentials_by_id(
    credentials_id: int,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get TISS credentials by ID"""
    credentials = tiss_service.get_credentials_by_id(credentials_id)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found"
        )
    return credentials


@router.put("/credentials/{credentials_id}", response_model=TISSCredentials)
async def update_credentials(
    credentials_id: int,
    credentials_data: TISSCredentialsUpdate,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Update TISS credentials"""
    credentials = tiss_service.update_credentials(credentials_id, credentials_data)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found"
        )
    return credentials


@router.post("/credentials/{credentials_id}/test", response_model=TISSCredentialsTestResponse)
async def test_credentials(
    credentials_id: int,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Test TISS credentials connection"""
    try:
        result = tiss_service.test_credentials(credentials_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test credentials: {str(e)}"
        )


# Doctor Codes Endpoints
@router.get("/doctor-codes", response_model=List[TISSDoctorCode])
async def get_doctor_codes(
    doctor_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get doctor codes"""
    try:
        doctor_codes = tiss_service.get_doctor_codes(doctor_id, operator_id)
        return doctor_codes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get doctor codes: {str(e)}"
        )


@router.post("/doctor-codes", response_model=TISSDoctorCode, status_code=status.HTTP_201_CREATED)
async def create_doctor_code(
    doctor_code_data: TISSDoctorCodeCreate,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Create doctor code"""
    try:
        doctor_code = tiss_service.create_doctor_code(doctor_code_data)
        return doctor_code
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create doctor code: {str(e)}"
        )


@router.put("/doctor-codes/{doctor_code_id}", response_model=TISSDoctorCode)
async def update_doctor_code(
    doctor_code_id: int,
    doctor_code_data: TISSDoctorCodeUpdate,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Update doctor code"""
    doctor_code = tiss_service.update_doctor_code(doctor_code_id, doctor_code_data)
    if not doctor_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor code not found"
        )
    return doctor_code


# Configuration Endpoints
@router.get("/configuration", response_model=TISSConfiguration)
async def get_configuration(
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get TISS configuration for the current tenant"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = tiss_service.get_configuration(tenant_id)
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="TISS configuration not found"
            )
        return configuration
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/configuration", response_model=TISSConfiguration, status_code=status.HTTP_201_CREATED)
async def create_or_update_configuration(
    config_data: TISSConfigurationCreate,
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Create or update TISS configuration"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = tiss_service.create_or_update_configuration(tenant_id, config_data)
        return configuration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update configuration: {str(e)}"
        )


# Dashboard and Status Endpoints
@router.get("/dashboard", response_model=TISSDashboardResponse)
async def get_dashboard_data(
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get TISS dashboard data"""
    try:
        tenant_id = get_tenant_id(request)
        dashboard_data = tiss_service.get_dashboard_data(tenant_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/operators-status", response_model=TISSOperatorsStatusResponse)
async def get_operators_status(
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get status of all TISS operators"""
    try:
        tenant_id = get_tenant_id(request)
        status_data = tiss_service.get_operators_status(tenant_id)
        return status_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operators status: {str(e)}"
        )


# Transaction Endpoints
@router.get("/transactions", response_model=List[TISSTransaction])
async def get_transactions(
    operator_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[str] = None,
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Get TISS transactions"""
    try:
        tenant_id = get_tenant_id(request)
        # This would be implemented in the service
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {str(e)}"
        )


@router.post("/transactions", response_model=TISSTransaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TISSTransactionCreate,
    request: Request = None,
    tiss_service: TISSService = Depends(get_tiss_service)
):
    """Create TISS transaction"""
    try:
        tenant_id = get_tenant_id(request)
        # This would be implemented in the service
        # For now, raise not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Transaction creation not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )
