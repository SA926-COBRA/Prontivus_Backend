"""
Advanced EMR API Endpoints
Handles Electronic Medical Records, Prescriptions, SADT, and ICD-10
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.database import get_db
from app.services.advanced_emr_service import AdvancedEMRService
from app.services.auth_service import AuthService
from app.schemas.advanced_emr import (
    ICD10CodeCreate, ICD10CodeUpdate, ICD10CodeInDB,
    PatientHistoryCreate, PatientHistoryUpdate, PatientHistoryInDB,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionInDB,
    PrescriptionMedicationCreate, PrescriptionTypeCreate, PrescriptionTypeInDB,
    SADTRequestCreate, SADTRequestUpdate, SADTRequestInDB,
    PatientHistorySearch, PrescriptionSearch, SADTRequestSearch,
    PrescriptionStatus, SADTServiceType, SADTUrgencyLevel
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ICD-10 Endpoints
@router.post("/icd10-codes", response_model=ICD10CodeInDB)
async def create_icd10_code(
    icd10_data: ICD10CodeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new ICD-10 code"""
    try:
        service = AdvancedEMRService(db)
        return service.create_icd10_code(icd10_data)
    except Exception as e:
        logger.error(f"Error creating ICD-10 code: {e}")
        raise HTTPException(status_code=500, detail="Error creating ICD-10 code")


@router.get("/icd10-codes", response_model=List[ICD10CodeInDB])
async def get_icd10_codes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get ICD-10 codes with optional search"""
    try:
        service = AdvancedEMRService(db)
        return service.get_icd10_codes(skip=skip, limit=limit, search=search)
    except Exception as e:
        logger.error(f"Error getting ICD-10 codes: {e}")
        raise HTTPException(status_code=500, detail="Error getting ICD-10 codes")


@router.post("/icd10-codes/import")
async def import_icd10_codes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Import ICD-10 codes from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        
        # Read and parse CSV file
        content = await file.read()
        csv_data = parse_csv_content(content.decode('utf-8'))
        
        service = AdvancedEMRService(db)
        imported_count = service.import_icd10_codes_from_csv(csv_data)
        
        return {"message": f"Successfully imported {imported_count} ICD-10 codes"}
    except Exception as e:
        logger.error(f"Error importing ICD-10 codes: {e}")
        raise HTTPException(status_code=500, detail="Error importing ICD-10 codes")


# Patient History Endpoints
@router.post("/patient-histories", response_model=PatientHistoryInDB)
async def create_patient_history(
    history_data: PatientHistoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new patient history entry"""
    try:
        service = AdvancedEMRService(db)
        return service.create_patient_history(history_data, current_user.id)
    except Exception as e:
        logger.error(f"Error creating patient history: {e}")
        raise HTTPException(status_code=500, detail="Error creating patient history")


@router.get("/patient-histories", response_model=List[PatientHistoryInDB])
async def get_patient_histories(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    diagnosis_code: Optional[str] = None,
    visit_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get patient histories with search filters"""
    try:
        search_params = PatientHistorySearch(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date_from=date_from,
            date_to=date_to,
            diagnosis_code=diagnosis_code,
            visit_type=visit_type
        )
        
        service = AdvancedEMRService(db)
        return service.get_patient_histories(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting patient histories: {e}")
        raise HTTPException(status_code=500, detail="Error getting patient histories")


@router.get("/patient-histories/{history_id}", response_model=PatientHistoryInDB)
async def get_patient_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get patient history by ID"""
    try:
        service = AdvancedEMRService(db)
        history = service.get_patient_history_by_id(history_id)
        if not history:
            raise HTTPException(status_code=404, detail="Patient history not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient history: {e}")
        raise HTTPException(status_code=500, detail="Error getting patient history")


# Prescription Endpoints
@router.post("/prescriptions", response_model=PrescriptionInDB)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new prescription"""
    try:
        service = AdvancedEMRService(db)
        return service.create_prescription(prescription_data, current_user.id)
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")
        raise HTTPException(status_code=500, detail="Error creating prescription")


@router.get("/prescriptions", response_model=List[PrescriptionInDB])
async def get_prescriptions(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    prescription_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[PrescriptionStatus] = None,
    is_signed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get prescriptions with search filters"""
    try:
        search_params = PrescriptionSearch(
            patient_id=patient_id,
            doctor_id=doctor_id,
            prescription_type=prescription_type,
            date_from=date_from,
            date_to=date_to,
            status=status,
            is_signed=is_signed
        )
        
        service = AdvancedEMRService(db)
        return service.get_prescriptions(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting prescriptions: {e}")
        raise HTTPException(status_code=500, detail="Error getting prescriptions")


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionInDB)
async def get_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get prescription by ID"""
    try:
        service = AdvancedEMRService(db)
        prescription = service.get_prescription_by_id(prescription_id)
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return prescription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription: {e}")
        raise HTTPException(status_code=500, detail="Error getting prescription")


@router.post("/prescriptions/{prescription_id}/sign")
async def sign_prescription(
    prescription_id: int,
    certificate_serial: str,
    signature_hash: str,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Digitally sign prescription with ICP-Brasil certificate"""
    try:
        service = AdvancedEMRService(db)
        prescription = service.sign_prescription(prescription_id, certificate_serial, signature_hash, current_user.id)
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return prescription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error signing prescription: {e}")
        raise HTTPException(status_code=500, detail="Error signing prescription")


@router.get("/prescriptions/verify/{prescription_number}")
async def verify_prescription(
    prescription_number: str,
    db: Session = Depends(get_db)
):
    """Verify prescription authenticity (public endpoint)"""
    try:
        service = AdvancedEMRService(db)
        return service.verify_prescription(prescription_number)
    except Exception as e:
        logger.error(f"Error verifying prescription: {e}")
        raise HTTPException(status_code=500, detail="Error verifying prescription")


# SADT Request Endpoints
@router.post("/sadt-requests", response_model=SADTRequestInDB)
async def create_sadt_request(
    sadt_data: SADTRequestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new SADT request"""
    try:
        service = AdvancedEMRService(db)
        return service.create_sadt_request(sadt_data)
    except Exception as e:
        logger.error(f"Error creating SADT request: {e}")
        raise HTTPException(status_code=500, detail="Error creating SADT request")


@router.get("/sadt-requests", response_model=List[SADTRequestInDB])
async def get_sadt_requests(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    service_type: Optional[SADTServiceType] = None,
    urgency_level: Optional[SADTUrgencyLevel] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get SADT requests with search filters"""
    try:
        search_params = SADTRequestSearch(
            patient_id=patient_id,
            doctor_id=doctor_id,
            service_type=service_type,
            urgency_level=urgency_level,
            date_from=date_from,
            date_to=date_to,
            status=status
        )
        
        service = AdvancedEMRService(db)
        return service.get_sadt_requests(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting SADT requests: {e}")
        raise HTTPException(status_code=500, detail="Error getting SADT requests")


# Prescription Type Endpoints
@router.post("/prescription-types", response_model=PrescriptionTypeInDB)
async def create_prescription_type(
    type_data: PrescriptionTypeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new prescription type"""
    try:
        service = AdvancedEMRService(db)
        return service.create_prescription_type(type_data)
    except Exception as e:
        logger.error(f"Error creating prescription type: {e}")
        raise HTTPException(status_code=500, detail="Error creating prescription type")


@router.get("/prescription-types", response_model=List[PrescriptionTypeInDB])
async def get_prescription_types(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get all active prescription types"""
    try:
        service = AdvancedEMRService(db)
        return service.get_prescription_types()
    except Exception as e:
        logger.error(f"Error getting prescription types: {e}")
        raise HTTPException(status_code=500, detail="Error getting prescription types")


# Helper function for CSV parsing
def parse_csv_content(content: str) -> List[dict]:
    """Parse CSV content into list of dictionaries"""
    lines = content.strip().split('\n')
    if not lines:
        return []
    
    headers = [h.strip() for h in lines[0].split(',')]
    data = []
    
    for line in lines[1:]:
        if line.strip():
            values = [v.strip() for v in line.split(',')]
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))
    
    return data