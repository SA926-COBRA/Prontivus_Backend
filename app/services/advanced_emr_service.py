"""
Advanced EMR Service Layer - Core Functions
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
import json
import logging

from app.models.advanced_emr import (
    ICD10Code, PatientHistory, Prescription, PrescriptionMedication,
    PrescriptionType, SADTRequest, PrescriptionAuditLog
)
from app.schemas.advanced_emr import (
    ICD10CodeCreate, ICD10CodeUpdate, ICD10CodeInDB,
    PatientHistoryCreate, PatientHistoryUpdate, PatientHistoryInDB,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionInDB,
    PrescriptionMedicationCreate, PrescriptionTypeCreate, PrescriptionTypeInDB,
    SADTRequestCreate, SADTRequestUpdate, SADTRequestInDB,
    PrescriptionAuditLogCreate, PrescriptionAuditLogInDB,
    PatientHistorySearch, PrescriptionSearch, SADTRequestSearch,
    PrescriptionStatus, SADTServiceType, SADTUrgencyLevel
)

logger = logging.getLogger(__name__)


class AdvancedEMRService:
    def __init__(self, db: Session):
        self.db = db

    # ICD-10 Management
    def create_icd10_code(self, icd10_data: ICD10CodeCreate) -> ICD10CodeInDB:
        """Create a new ICD-10 code"""
        try:
            icd10_code = ICD10Code(**icd10_data.dict())
            self.db.add(icd10_code)
            self.db.commit()
            self.db.refresh(icd10_code)
            return ICD10CodeInDB.from_orm(icd10_code)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating ICD-10 code: {e}")
            raise

    def get_icd10_codes(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[ICD10CodeInDB]:
        """Get ICD-10 codes with optional search"""
        query = self.db.query(ICD10Code).filter(ICD10Code.is_active == True)
        
        if search:
            query = query.filter(
                or_(
                    ICD10Code.code.ilike(f"%{search}%"),
                    ICD10Code.description.ilike(f"%{search}%")
                )
            )
        
        codes = query.offset(skip).limit(limit).all()
        return [ICD10CodeInDB.from_orm(code) for code in codes]

    def import_icd10_codes_from_csv(self, csv_data: List[Dict[str, Any]]) -> int:
        """Import ICD-10 codes from CSV data"""
        imported_count = 0
        try:
            for row in csv_data:
                existing = self.db.query(ICD10Code).filter(ICD10Code.code == row['code']).first()
                if not existing:
                    icd10_code = ICD10Code(
                        code=row['code'],
                        description=row['description'],
                        category=row.get('category'),
                        subcategory=row.get('subcategory'),
                        is_active=True
                    )
                    self.db.add(icd10_code)
                    imported_count += 1
            
            self.db.commit()
            logger.info(f"Imported {imported_count} ICD-10 codes from CSV")
            return imported_count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error importing ICD-10 codes: {e}")
            raise

    # Patient History Management
    def create_patient_history(self, history_data: PatientHistoryCreate, user_id: int) -> PatientHistoryInDB:
        """Create a new patient history entry"""
        try:
            history_dict = history_data.dict()
            history_dict['created_by'] = user_id
            history_dict['updated_by'] = user_id
            
            if history_dict.get('vital_signs'):
                history_dict['vital_signs'] = history_dict['vital_signs'].dict()
            
            patient_history = PatientHistory(**history_dict)
            self.db.add(patient_history)
            self.db.commit()
            self.db.refresh(patient_history)
            return PatientHistoryInDB.from_orm(patient_history)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating patient history: {e}")
            raise

    def get_patient_histories(self, search_params: PatientHistorySearch, skip: int = 0, limit: int = 100) -> List[PatientHistoryInDB]:
        """Get patient histories with search filters"""
        query = self.db.query(PatientHistory)
        
        if search_params.patient_id:
            query = query.filter(PatientHistory.patient_id == search_params.patient_id)
        if search_params.doctor_id:
            query = query.filter(PatientHistory.doctor_id == search_params.doctor_id)
        if search_params.date_from:
            query = query.filter(PatientHistory.visit_date >= search_params.date_from)
        if search_params.date_to:
            query = query.filter(PatientHistory.visit_date <= search_params.date_to)
        if search_params.diagnosis_code:
            query = query.filter(PatientHistory.primary_diagnosis_code == search_params.diagnosis_code)
        
        histories = query.order_by(desc(PatientHistory.visit_date)).offset(skip).limit(limit).all()
        return [PatientHistoryInDB.from_orm(history) for history in histories]

    # Prescription Management
    def generate_prescription_number(self) -> str:
        """Generate unique prescription number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"RX{timestamp}{random_suffix}"

    def create_prescription(self, prescription_data: PrescriptionCreate, user_id: int) -> PrescriptionInDB:
        """Create a new prescription"""
        try:
            prescription_number = self.generate_prescription_number()
            prescription_dict = prescription_data.dict()
            prescription_dict['prescription_number'] = prescription_number
            prescription_dict['status'] = PrescriptionStatus.DRAFT
            
            medications_data = prescription_dict.pop('medications', [])
            prescription = Prescription(**prescription_dict)
            self.db.add(prescription)
            self.db.flush()
            
            for med_data in medications_data:
                med_data['prescription_id'] = prescription.id
                medication = PrescriptionMedication(**med_data)
                self.db.add(medication)
            
            audit_log = PrescriptionAuditLog(
                prescription_id=prescription.id,
                user_id=user_id,
                action="created",
                description="Prescription created"
            )
            self.db.add(audit_log)
            
            self.db.commit()
            self.db.refresh(prescription)
            return PrescriptionInDB.from_orm(prescription)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating prescription: {e}")
            raise

    def sign_prescription(self, prescription_id: int, certificate_serial: str, signature_hash: str, user_id: int) -> Optional[PrescriptionInDB]:
        """Digitally sign prescription with ICP-Brasil certificate"""
        prescription = self.db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not prescription:
            return None
        
        prescription.is_digitally_signed = True
        prescription.certificate_serial = certificate_serial
        prescription.signature_timestamp = datetime.utcnow()
        prescription.signature_hash = signature_hash
        prescription.signature_valid = True
        prescription.status = PrescriptionStatus.SIGNED
        
        qr_data = {
            "prescription_number": prescription.prescription_number,
            "signature_hash": signature_hash,
            "timestamp": prescription.signature_timestamp.isoformat(),
            "verification_url": f"/verify-prescription/{prescription.prescription_number}"
        }
        prescription.qr_code_data = json.dumps(qr_data)
        prescription.verification_url = qr_data["verification_url"]
        
        audit_log = PrescriptionAuditLog(
            prescription_id=prescription_id,
            user_id=user_id,
            action="signed",
            description=f"Prescription digitally signed with certificate {certificate_serial}"
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(prescription)
        return PrescriptionInDB.from_orm(prescription)

    def verify_prescription(self, prescription_number: str) -> Dict[str, Any]:
        """Verify prescription authenticity"""
        prescription = self.db.query(Prescription).filter(Prescription.prescription_number == prescription_number).first()
        if not prescription:
            return {"valid": False, "error": "Prescription not found"}
        
        if not prescription.is_digitally_signed:
            return {"valid": False, "error": "Prescription not digitally signed"}
        
        if not prescription.signature_valid:
            return {"valid": False, "error": "Invalid signature"}
        
        return {
            "valid": True,
            "prescription": prescription,
            "signature_timestamp": prescription.signature_timestamp,
            "certificate_serial": prescription.certificate_serial
        }

    # SADT Request Management
    def generate_sadt_request_number(self) -> str:
        """Generate unique SADT request number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:6].upper()
        return f"SADT{timestamp}{random_suffix}"

    def create_sadt_request(self, sadt_data: SADTRequestCreate) -> SADTRequestInDB:
        """Create a new SADT request"""
        try:
            request_number = self.generate_sadt_request_number()
            sadt_dict = sadt_data.dict()
            sadt_dict['request_number'] = request_number
            sadt_dict['status'] = "draft"
            
            sadt_request = SADTRequest(**sadt_dict)
            self.db.add(sadt_request)
            self.db.commit()
            self.db.refresh(sadt_request)
            return SADTRequestInDB.from_orm(sadt_request)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating SADT request: {e}")
            raise

    def get_sadt_requests(self, search_params: SADTRequestSearch, skip: int = 0, limit: int = 100) -> List[SADTRequestInDB]:
        """Get SADT requests with search filters"""
        query = self.db.query(SADTRequest)
        
        if search_params.patient_id:
            query = query.filter(SADTRequest.patient_id == search_params.patient_id)
        if search_params.doctor_id:
            query = query.filter(SADTRequest.doctor_id == search_params.doctor_id)
        if search_params.service_type:
            query = query.filter(SADTRequest.service_type == search_params.service_type)
        if search_params.date_from:
            query = query.filter(SADTRequest.request_date >= search_params.date_from)
        if search_params.date_to:
            query = query.filter(SADTRequest.request_date <= search_params.date_to)
        
        requests = query.order_by(desc(SADTRequest.request_date)).offset(skip).limit(limit).all()
        return [SADTRequestInDB.from_orm(request) for request in requests]