from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database.database import get_db
from app.models.advanced_emr import (
    ControlledPrescription, PrescriptionRefill, SADT, SADTICDCode,
    ICDCode, MedicalProcedure, HealthPlan, PrescriptionAudit, SADTAudit
)
from app.models.user import User
from app.schemas.advanced_emr import (
    ControlledPrescriptionCreate, ControlledPrescriptionUpdate, ControlledPrescription as ControlledPrescriptionSchema,
    PrescriptionRefillCreate, PrescriptionRefill as PrescriptionRefillSchema,
    SADTCreate, SADTUpdate, SADT as SADTSchema,
    SADTICDCodeCreate, SADTICDCodeUpdate, SADTICDCode as SADTICDCodeSchema,
    ICDCodeCreate, ICDCodeUpdate, ICDCode as ICDCodeSchema,
    MedicalProcedureCreate, MedicalProcedureUpdate, MedicalProcedure as MedicalProcedureSchema,
    HealthPlanCreate, HealthPlanUpdate, HealthPlan as HealthPlanSchema,
    PrescriptionAudit as PrescriptionAuditSchema,
    SADTAudit as SADTAuditSchema,
    PrescriptionSearchRequest, SADTSearchRequest, ICDCodeSearchRequest,
    PrescriptionDispenseRequest, SADTAuthorizationRequest,
    PrescriptionSummary, SADTSummary, ICDCodeHierarchy
)
from app.services.auth_service import AuthService
from app.services.advanced_emr_service import AdvancedEMRService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Controlled Prescription endpoints
@router.get("/prescriptions", response_model=List[ControlledPrescriptionSchema], summary="Get controlled prescriptions")
async def get_controlled_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    control_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    medication_name: Optional[str] = Query(None)
):
    """Get controlled prescriptions with filtering options"""
    try:
        emr_service = AdvancedEMRService(db)
        request = PrescriptionSearchRequest(
            patient_id=patient_id,
            doctor_id=doctor_id,
            control_level=control_level,
            status=status,
            medication_name=medication_name,
            skip=skip,
            limit=limit
        )
        prescriptions = emr_service.search_prescriptions(request)
        return prescriptions
    except Exception as e:
        logger.error(f"Error getting controlled prescriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prescriptions: {str(e)}"
        )

@router.get("/prescriptions/{prescription_id}", response_model=ControlledPrescriptionSchema, summary="Get controlled prescription by ID")
async def get_controlled_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific controlled prescription by ID"""
    prescription = db.query(ControlledPrescription).filter(
        ControlledPrescription.id == prescription_id
    ).first()
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlled prescription not found")
    return prescription

@router.post("/prescriptions", response_model=ControlledPrescriptionSchema, status_code=status.HTTP_201_CREATED, summary="Create controlled prescription")
async def create_controlled_prescription(
    prescription_data: ControlledPrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new controlled prescription"""
    try:
        emr_service = AdvancedEMRService(db)
        prescription = emr_service.create_prescription(prescription_data.dict(), current_user.id)
        return prescription
    except Exception as e:
        logger.error(f"Error creating controlled prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prescription: {str(e)}"
        )

@router.put("/prescriptions/{prescription_id}", response_model=ControlledPrescriptionSchema, summary="Update controlled prescription")
async def update_controlled_prescription(
    prescription_id: int,
    prescription_data: ControlledPrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a controlled prescription"""
    try:
        emr_service = AdvancedEMRService(db)
        update_data = prescription_data.dict(exclude_unset=True)
        prescription = emr_service.update_prescription(prescription_id, update_data, current_user.id)
        return prescription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating controlled prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prescription: {str(e)}"
        )

@router.post("/prescriptions/{prescription_id}/dispense", response_model=PrescriptionRefillSchema, summary="Dispense prescription")
async def dispense_prescription(
    prescription_id: int,
    request: PrescriptionDispenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dispense a controlled prescription"""
    try:
        request.prescription_id = prescription_id
        emr_service = AdvancedEMRService(db)
        refill = emr_service.dispense_prescription(request, current_user.id)
        return refill
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error dispensing prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispense prescription: {str(e)}"
        )

@router.get("/prescriptions/{prescription_id}/refills", response_model=List[PrescriptionRefillSchema], summary="Get prescription refills")
async def get_prescription_refills(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get refills for a specific prescription"""
    refills = db.query(PrescriptionRefill).filter(
        PrescriptionRefill.prescription_id == prescription_id
    ).order_by(PrescriptionRefill.refill_date.desc()).all()
    return refills

@router.get("/prescriptions/summary", response_model=PrescriptionSummary, summary="Get prescription summary")
async def get_prescription_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get prescription summary statistics"""
    try:
        emr_service = AdvancedEMRService(db)
        summary = emr_service.get_prescription_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting prescription summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prescription summary: {str(e)}"
        )

# SADT endpoints
@router.get("/sadt", response_model=List[SADTSchema], summary="Get SADT requests")
async def get_sadt_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    sadt_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    procedure_name: Optional[str] = Query(None)
):
    """Get SADT requests with filtering options"""
    try:
        emr_service = AdvancedEMRService(db)
        request = SADTSearchRequest(
            patient_id=patient_id,
            doctor_id=doctor_id,
            sadt_type=sadt_type,
            status=status,
            procedure_name=procedure_name,
            skip=skip,
            limit=limit
        )
        sadt_requests = emr_service.search_sadt(request)
        return sadt_requests
    except Exception as e:
        logger.error(f"Error getting SADT requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SADT requests: {str(e)}"
        )

@router.get("/sadt/{sadt_id}", response_model=SADTSchema, summary="Get SADT request by ID")
async def get_sadt_request(
    sadt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific SADT request by ID"""
    sadt = db.query(SADT).filter(SADT.id == sadt_id).first()
    if not sadt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SADT request not found")
    return sadt

@router.post("/sadt", response_model=SADTSchema, status_code=status.HTTP_201_CREATED, summary="Create SADT request")
async def create_sadt_request(
    sadt_data: SADTCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new SADT request"""
    try:
        emr_service = AdvancedEMRService(db)
        sadt = emr_service.create_sadt(sadt_data.dict(), current_user.id)
        return sadt
    except Exception as e:
        logger.error(f"Error creating SADT request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SADT request: {str(e)}"
        )

@router.put("/sadt/{sadt_id}", response_model=SADTSchema, summary="Update SADT request")
async def update_sadt_request(
    sadt_id: int,
    sadt_data: SADTUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a SADT request"""
    try:
        emr_service = AdvancedEMRService(db)
        update_data = sadt_data.dict(exclude_unset=True)
        sadt = emr_service.update_sadt(sadt_id, update_data, current_user.id)
        return sadt
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating SADT request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SADT request: {str(e)}"
        )

@router.post("/sadt/{sadt_id}/authorize", response_model=SADTSchema, summary="Authorize SADT request")
async def authorize_sadt_request(
    sadt_id: int,
    request: SADTAuthorizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Authorize a SADT request"""
    try:
        request.sadt_id = sadt_id
        emr_service = AdvancedEMRService(db)
        sadt = emr_service.authorize_sadt(request)
        return sadt
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error authorizing SADT request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authorize SADT request: {str(e)}"
        )

@router.get("/sadt/{sadt_id}/icd-codes", response_model=List[SADTICDCodeSchema], summary="Get SADT ICD codes")
async def get_sadt_icd_codes(
    sadt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ICD codes for a specific SADT request"""
    icd_codes = db.query(SADTICDCode).filter(
        SADTICDCode.sadt_id == sadt_id
    ).all()
    return icd_codes

@router.post("/sadt/{sadt_id}/icd-codes", response_model=SADTICDCodeSchema, status_code=status.HTTP_201_CREATED, summary="Add ICD code to SADT")
async def add_sadt_icd_code(
    sadt_id: int,
    icd_code_data: SADTICDCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an ICD code to a SADT request"""
    icd_code_data.sadt_id = sadt_id
    icd_code = SADTICDCode(**icd_code_data.dict())
    
    db.add(icd_code)
    db.commit()
    db.refresh(icd_code)
    return icd_code

@router.get("/sadt/summary", response_model=SADTSummary, summary="Get SADT summary")
async def get_sadt_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SADT summary statistics"""
    try:
        emr_service = AdvancedEMRService(db)
        summary = emr_service.get_sadt_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting SADT summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SADT summary: {str(e)}"
        )

# ICD Code endpoints
@router.get("/icd-codes", response_model=List[ICDCodeSchema], summary="Get ICD codes")
async def get_icd_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    code: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    parent_code: Optional[str] = Query(None)
):
    """Get ICD codes with filtering options"""
    try:
        emr_service = AdvancedEMRService(db)
        request = ICDCodeSearchRequest(
            code=code,
            description=description,
            category=category,
            parent_code=parent_code,
            skip=skip,
            limit=limit
        )
        icd_codes = emr_service.search_icd_codes(request)
        return icd_codes
    except Exception as e:
        logger.error(f"Error getting ICD codes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ICD codes: {str(e)}"
        )

@router.get("/icd-codes/{icd_code_id}", response_model=ICDCodeSchema, summary="Get ICD code by ID")
async def get_icd_code(
    icd_code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific ICD code by ID"""
    icd_code = db.query(ICDCode).filter(ICDCode.id == icd_code_id).first()
    if not icd_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ICD code not found")
    return icd_code

@router.get("/icd-codes/hierarchy", response_model=List[ICDCodeHierarchy], summary="Get ICD code hierarchy")
async def get_icd_hierarchy(
    parent_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ICD code hierarchy"""
    try:
        emr_service = AdvancedEMRService(db)
        hierarchy = emr_service.get_icd_hierarchy(parent_code)
        return hierarchy
    except Exception as e:
        logger.error(f"Error getting ICD hierarchy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ICD hierarchy: {str(e)}"
        )

# Medical Procedure endpoints
@router.get("/procedures", response_model=List[MedicalProcedureSchema], summary="Get medical procedures")
async def get_medical_procedures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    procedure_type: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get medical procedures with filtering options"""
    query = db.query(MedicalProcedure)
    
    if procedure_type:
        query = query.filter(MedicalProcedure.procedure_type == procedure_type)
    
    if specialty:
        query = query.filter(MedicalProcedure.specialty == specialty)
    
    if is_active is not None:
        query = query.filter(MedicalProcedure.is_active == is_active)
    
    procedures = query.offset(skip).limit(limit).all()
    return procedures

@router.get("/procedures/{procedure_id}", response_model=MedicalProcedureSchema, summary="Get medical procedure by ID")
async def get_medical_procedure(
    procedure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific medical procedure by ID"""
    procedure = db.query(MedicalProcedure).filter(MedicalProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical procedure not found")
    return procedure

@router.post("/procedures", response_model=MedicalProcedureSchema, status_code=status.HTTP_201_CREATED, summary="Create medical procedure")
async def create_medical_procedure(
    procedure_data: MedicalProcedureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new medical procedure"""
    procedure = MedicalProcedure(**procedure_data.dict())
    
    db.add(procedure)
    db.commit()
    db.refresh(procedure)
    return procedure

@router.put("/procedures/{procedure_id}", response_model=MedicalProcedureSchema, summary="Update medical procedure")
async def update_medical_procedure(
    procedure_id: int,
    procedure_data: MedicalProcedureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a medical procedure"""
    procedure = db.query(MedicalProcedure).filter(MedicalProcedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical procedure not found")
    
    update_data = procedure_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procedure, field, value)
    
    db.commit()
    db.refresh(procedure)
    return procedure

# Health Plan endpoints
@router.get("/health-plans", response_model=List[HealthPlanSchema], summary="Get health plans")
async def get_health_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    plan_type: Optional[str] = Query(None),
    coverage_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get health plans with filtering options"""
    query = db.query(HealthPlan)
    
    if plan_type:
        query = query.filter(HealthPlan.plan_type == plan_type)
    
    if coverage_type:
        query = query.filter(HealthPlan.coverage_type == coverage_type)
    
    if is_active is not None:
        query = query.filter(HealthPlan.is_active == is_active)
    
    health_plans = query.offset(skip).limit(limit).all()
    return health_plans

@router.get("/health-plans/{health_plan_id}", response_model=HealthPlanSchema, summary="Get health plan by ID")
async def get_health_plan(
    health_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific health plan by ID"""
    health_plan = db.query(HealthPlan).filter(HealthPlan.id == health_plan_id).first()
    if not health_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan not found")
    return health_plan

@router.post("/health-plans", response_model=HealthPlanSchema, status_code=status.HTTP_201_CREATED, summary="Create health plan")
async def create_health_plan(
    health_plan_data: HealthPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new health plan"""
    health_plan = HealthPlan(**health_plan_data.dict())
    
    db.add(health_plan)
    db.commit()
    db.refresh(health_plan)
    return health_plan

@router.put("/health-plans/{health_plan_id}", response_model=HealthPlanSchema, summary="Update health plan")
async def update_health_plan(
    health_plan_id: int,
    health_plan_data: HealthPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a health plan"""
    health_plan = db.query(HealthPlan).filter(HealthPlan.id == health_plan_id).first()
    if not health_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health plan not found")
    
    update_data = health_plan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(health_plan, field, value)
    
    db.commit()
    db.refresh(health_plan)
    return health_plan

# Audit endpoints
@router.get("/prescriptions/{prescription_id}/audit", response_model=List[PrescriptionAuditSchema], summary="Get prescription audit trail")
async def get_prescription_audit(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific prescription"""
    audit_records = db.query(PrescriptionAudit).filter(
        PrescriptionAudit.prescription_id == prescription_id
    ).order_by(PrescriptionAudit.performed_at.desc()).all()
    return audit_records

@router.get("/sadt/{sadt_id}/audit", response_model=List[SADTAuditSchema], summary="Get SADT audit trail")
async def get_sadt_audit(
    sadt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific SADT request"""
    audit_records = db.query(SADTAudit).filter(
        SADTAudit.sadt_id == sadt_id
    ).order_by(SADTAudit.performed_at.desc()).all()
    return audit_records

# Health check endpoint
@router.get("/health", summary="Advanced EMR service health check")
async def health_check():
    """Check the health of the Advanced EMR service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "advanced_emr",
        "features": {
            "controlled_prescriptions": True,
            "sadt_management": True,
            "icd_codes": True,
            "medical_procedures": True,
            "health_plans": True,
            "audit_trail": True
        }
    }
