"""
Digital Prescription API Endpoints
API endpoints for digital prescription with ICP-Brasil signature
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.services.digital_prescription_service import PrescriptionService
from app.schemas.digital_prescription import (
    DigitalPrescription, DigitalPrescriptionCreate, DigitalPrescriptionUpdate,
    PrescriptionMedication, PrescriptionConfiguration, PrescriptionConfigurationCreate, PrescriptionConfigurationUpdate,
    PrescriptionSignRequest, PrescriptionSignResponse,
    PrescriptionDeliveryRequest, PrescriptionDeliveryResponse,
    PrescriptionVerificationRequest, PrescriptionVerificationResponse,
    PrescriptionDashboardResponse, PrescriptionsResponse
)
from app.services.auth_service import AuthService

router = APIRouter()


def get_prescription_service(db: Session = Depends(get_db)) -> PrescriptionService:
    """Get prescription service instance"""
    return PrescriptionService(db)


def get_tenant_id(request: Request) -> int:
    """Extract tenant ID from request (simplified for now)"""
    return 1  # Default tenant ID


# Prescription Management Endpoints
@router.get("/prescriptions", response_model=PrescriptionsResponse)
async def get_prescriptions(
    status: Optional[str] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    request: Request = None,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Get digital prescriptions with pagination"""
    try:
        tenant_id = get_tenant_id(request)
        prescriptions_response = prescription_service.get_prescriptions(
            tenant_id=tenant_id,
            status=status,
            doctor_id=doctor_id,
            patient_id=patient_id,
            page=page,
            page_size=page_size
        )
        return prescriptions_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prescriptions: {str(e)}"
        )


@router.post("/prescriptions", response_model=DigitalPrescription, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    prescription_data: DigitalPrescriptionCreate,
    request: Request = None,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Create a new digital prescription"""
    try:
        tenant_id = get_tenant_id(request)
        prescription = prescription_service.create_prescription(tenant_id, prescription_data)
        return prescription
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prescription: {str(e)}"
        )


@router.get("/prescriptions/{prescription_id}", response_model=DigitalPrescription)
async def get_prescription(
    prescription_id: str,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Get digital prescription by prescription ID"""
    prescription = prescription_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    return prescription


@router.put("/prescriptions/{prescription_id}", response_model=DigitalPrescription)
async def update_prescription(
    prescription_id: str,
    prescription_data: DigitalPrescriptionUpdate,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Update digital prescription"""
    prescription = prescription_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    
    # Update prescription
    update_dict = prescription_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(prescription, field) and value is not None:
            setattr(prescription, field, value)
    
    prescription_service.db.commit()
    prescription_service.db.refresh(prescription)
    
    return prescription


# Digital Signature Endpoints
@router.post("/prescriptions/{prescription_id}/sign", response_model=PrescriptionSignResponse)
async def sign_prescription(
    prescription_id: str,
    sign_request: PrescriptionSignRequest,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Sign a digital prescription"""
    result = prescription_service.sign_prescription(prescription_id, sign_request)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result


# Delivery Endpoints
@router.post("/prescriptions/{prescription_id}/deliver", response_model=PrescriptionDeliveryResponse)
async def deliver_prescription(
    prescription_id: str,
    delivery_request: PrescriptionDeliveryRequest,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Deliver a prescription to patient"""
    result = prescription_service.deliver_prescription(prescription_id, delivery_request)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result


# Verification Endpoints
@router.post("/prescriptions/verify", response_model=PrescriptionVerificationResponse)
async def verify_prescription(
    verification_request: PrescriptionVerificationRequest,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Verify a prescription using QR code"""
    result = prescription_service.verify_prescription(verification_request)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message
        )
    
    return result


# Configuration Endpoints
@router.get("/configuration", response_model=PrescriptionConfiguration)
async def get_configuration(
    request: Request = None,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Get prescription configuration for the current tenant"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = prescription_service.get_configuration(tenant_id)
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription configuration not found"
            )
        return configuration
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/configuration", response_model=PrescriptionConfiguration, status_code=status.HTTP_201_CREATED)
async def create_or_update_configuration(
    config_data: PrescriptionConfigurationCreate,
    request: Request = None,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Create or update prescription configuration"""
    try:
        tenant_id = get_tenant_id(request)
        configuration = prescription_service.create_or_update_configuration(tenant_id, config_data)
        return configuration
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update configuration: {str(e)}"
        )


# Dashboard Endpoints
@router.get("/dashboard", response_model=PrescriptionDashboardResponse)
async def get_dashboard_data(
    request: Request = None,
    prescription_service: PrescriptionService = Depends(get_prescription_service)
):
    """Get prescription dashboard data"""
    try:
        tenant_id = get_tenant_id(request)
        dashboard_data = prescription_service.get_dashboard_data(tenant_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


# Health Check Endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for digital prescription service"""
    return {
        "status": "healthy",
        "service": "digital-prescription",
        "timestamp": datetime.now().isoformat()
    }
