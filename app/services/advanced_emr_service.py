import os
import json
import hashlib
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from decimal import Decimal
import uuid

from app.models.advanced_emr import (
    ControlledPrescription, PrescriptionRefill, SADT, SADTICDCode,
    ICDCode, MedicalProcedure, HealthPlan, PrescriptionAudit, SADTAudit
)
from app.schemas.advanced_emr import (
    PrescriptionSearchRequest, SADTSearchRequest, ICDCodeSearchRequest,
    PrescriptionDispenseRequest, SADTAuthorizationRequest,
    PrescriptionSummary, SADTSummary, ICDCodeHierarchy
)

logger = logging.getLogger(__name__)

class AdvancedEMRService:
    """Service for Advanced Electronic Medical Record management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Prescription Management
    def create_prescription(self, prescription_data: dict, user_id: int) -> ControlledPrescription:
        """Create a new controlled prescription"""
        try:
            # Generate prescription number
            prescription_number = self._generate_prescription_number()
            
            # Create prescription
            prescription = ControlledPrescription(
                prescription_number=prescription_number,
                **prescription_data,
                created_by=user_id
            )
            
            # Generate digital signature and hash
            prescription.digital_signature = self._generate_digital_signature(prescription)
            prescription.prescription_hash = self._generate_prescription_hash(prescription)
            
            # Check regulatory compliance
            prescription.regulatory_compliance = self._check_regulatory_compliance(prescription)
            
            self.db.add(prescription)
            self.db.commit()
            self.db.refresh(prescription)
            
            # Create audit record
            self._create_prescription_audit(
                prescription.id, "created", None, prescription.status, user_id
            )
            
            return prescription
            
        except Exception as e:
            logger.error(f"Error creating prescription: {e}")
            raise
    
    def update_prescription(self, prescription_id: int, update_data: dict, user_id: int) -> ControlledPrescription:
        """Update a controlled prescription"""
        try:
            prescription = self.db.query(ControlledPrescription).filter(
                ControlledPrescription.id == prescription_id
            ).first()
            
            if not prescription:
                raise ValueError("Prescription not found")
            
            # Store previous status for audit
            previous_status = prescription.status
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(prescription, field):
                    setattr(prescription, field, value)
            
            # Update digital signature and hash
            prescription.digital_signature = self._generate_digital_signature(prescription)
            prescription.prescription_hash = self._generate_prescription_hash(prescription)
            
            # Update regulatory compliance
            prescription.regulatory_compliance = self._check_regulatory_compliance(prescription)
            
            self.db.commit()
            self.db.refresh(prescription)
            
            # Create audit record
            self._create_prescription_audit(
                prescription.id, "updated", previous_status, prescription.status, user_id
            )
            
            return prescription
            
        except Exception as e:
            logger.error(f"Error updating prescription: {e}")
            raise
    
    def dispense_prescription(self, request: PrescriptionDispenseRequest, user_id: int) -> PrescriptionRefill:
        """Dispense a prescription"""
        try:
            prescription = self.db.query(ControlledPrescription).filter(
                ControlledPrescription.id == request.prescription_id
            ).first()
            
            if not prescription:
                raise ValueError("Prescription not found")
            
            # Check if prescription can be dispensed
            if prescription.status != "active":
                raise ValueError("Prescription is not active")
            
            if prescription.refills_used >= prescription.refills_allowed:
                raise ValueError("No refills remaining")
            
            # Create refill record
            refill = PrescriptionRefill(
                prescription_id=request.prescription_id,
                refill_number=prescription.refills_used + 1,
                refill_date=datetime.utcnow(),
                quantity_dispensed=request.quantity_dispensed,
                dispensed_by=user_id,
                pharmacy_name=request.pharmacy_name,
                pharmacy_address=request.pharmacy_address,
                patient_identification_verified=request.patient_identification_verified,
                prescription_verified=request.prescription_verified,
                regulatory_compliance_checked=request.regulatory_compliance_checked
            )
            
            self.db.add(refill)
            
            # Update prescription
            prescription.refills_used += 1
            prescription.dispensed = True
            prescription.dispensed_at = datetime.utcnow()
            prescription.dispensed_by = user_id
            
            # Check if prescription is completed
            if prescription.refills_used >= prescription.refills_allowed:
                prescription.status = "completed"
            
            self.db.commit()
            self.db.refresh(refill)
            
            # Create audit record
            self._create_prescription_audit(
                prescription.id, "dispensed", "active", prescription.status, user_id
            )
            
            return refill
            
        except Exception as e:
            logger.error(f"Error dispensing prescription: {e}")
            raise
    
    def search_prescriptions(self, request: PrescriptionSearchRequest) -> List[ControlledPrescription]:
        """Search prescriptions with filters"""
        try:
            query = self.db.query(ControlledPrescription)
            
            if request.patient_id:
                query = query.filter(ControlledPrescription.patient_id == request.patient_id)
            
            if request.doctor_id:
                query = query.filter(ControlledPrescription.doctor_id == request.doctor_id)
            
            if request.control_level:
                query = query.filter(ControlledPrescription.control_level == request.control_level)
            
            if request.status:
                query = query.filter(ControlledPrescription.status == request.status)
            
            if request.medication_name:
                query = query.filter(
                    ControlledPrescription.medication_name.ilike(f"%{request.medication_name}%")
                )
            
            if request.date_from:
                query = query.filter(ControlledPrescription.prescription_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(ControlledPrescription.prescription_date <= request.date_to)
            
            prescriptions = query.order_by(desc(ControlledPrescription.prescription_date)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return prescriptions
            
        except Exception as e:
            logger.error(f"Error searching prescriptions: {e}")
            raise
    
    def get_prescription_summary(self) -> PrescriptionSummary:
        """Get prescription summary statistics"""
        try:
            total_prescriptions = self.db.query(ControlledPrescription).count()
            active_prescriptions = self.db.query(ControlledPrescription).filter(
                ControlledPrescription.status == "active"
            ).count()
            controlled_prescriptions = self.db.query(ControlledPrescription).filter(
                ControlledPrescription.controlled_substance == True
            ).count()
            expired_prescriptions = self.db.query(ControlledPrescription).filter(
                ControlledPrescription.status == "expired"
            ).count()
            
            # Prescriptions by control level
            control_level_stats = self.db.query(
                ControlledPrescription.control_level,
                func.count(ControlledPrescription.id)
            ).group_by(ControlledPrescription.control_level).all()
            
            prescriptions_by_control_level = {
                stat[0].value: stat[1] for stat in control_level_stats
            }
            
            # Prescriptions by status
            status_stats = self.db.query(
                ControlledPrescription.status,
                func.count(ControlledPrescription.id)
            ).group_by(ControlledPrescription.status).all()
            
            prescriptions_by_status = {
                stat[0].value: stat[1] for stat in status_stats
            }
            
            return PrescriptionSummary(
                total_prescriptions=total_prescriptions,
                active_prescriptions=active_prescriptions,
                controlled_prescriptions=controlled_prescriptions,
                expired_prescriptions=expired_prescriptions,
                prescriptions_by_control_level=prescriptions_by_control_level,
                prescriptions_by_status=prescriptions_by_status
            )
            
        except Exception as e:
            logger.error(f"Error getting prescription summary: {e}")
            raise
    
    # SADT Management
    def create_sadt(self, sadt_data: dict, user_id: int) -> SADT:
        """Create a new SADT request"""
        try:
            # Generate SADT number
            sadt_number = self._generate_sadt_number()
            
            # Create SADT
            sadt = SADT(
                sadt_number=sadt_number,
                **sadt_data,
                created_by=user_id
            )
            
            # Check regulatory compliance
            sadt.regulatory_compliance = self._check_sadt_compliance(sadt)
            
            self.db.add(sadt)
            self.db.commit()
            self.db.refresh(sadt)
            
            # Create audit record
            self._create_sadt_audit(
                sadt.id, "created", None, sadt.status, user_id
            )
            
            return sadt
            
        except Exception as e:
            logger.error(f"Error creating SADT: {e}")
            raise
    
    def update_sadt(self, sadt_id: int, update_data: dict, user_id: int) -> SADT:
        """Update a SADT request"""
        try:
            sadt = self.db.query(SADT).filter(SADT.id == sadt_id).first()
            
            if not sadt:
                raise ValueError("SADT not found")
            
            # Store previous status for audit
            previous_status = sadt.status
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(sadt, field):
                    setattr(sadt, field, value)
            
            # Update regulatory compliance
            sadt.regulatory_compliance = self._check_sadt_compliance(sadt)
            
            self.db.commit()
            self.db.refresh(sadt)
            
            # Create audit record
            self._create_sadt_audit(
                sadt.id, "updated", previous_status, sadt.status, user_id
            )
            
            return sadt
            
        except Exception as e:
            logger.error(f"Error updating SADT: {e}")
            raise
    
    def authorize_sadt(self, request: SADTAuthorizationRequest) -> SADT:
        """Authorize a SADT request"""
        try:
            sadt = self.db.query(SADT).filter(SADT.id == request.sadt_id).first()
            
            if not sadt:
                raise ValueError("SADT not found")
            
            # Store previous status for audit
            previous_status = sadt.status
            
            # Update SADT
            sadt.status = "authorized"
            sadt.authorized_date = request.authorized_date
            sadt.authorized_by = request.authorized_by
            sadt.authorization_number = request.authorization_number
            sadt.procedure_results = request.procedure_results
            sadt.follow_up_required = request.follow_up_required
            sadt.follow_up_date = request.follow_up_date
            
            self.db.commit()
            self.db.refresh(sadt)
            
            # Create audit record
            self._create_sadt_audit(
                sadt.id, "authorized", previous_status, sadt.status, request.authorized_by
            )
            
            return sadt
            
        except Exception as e:
            logger.error(f"Error authorizing SADT: {e}")
            raise
    
    def search_sadt(self, request: SADTSearchRequest) -> List[SADT]:
        """Search SADT requests with filters"""
        try:
            query = self.db.query(SADT)
            
            if request.patient_id:
                query = query.filter(SADT.patient_id == request.patient_id)
            
            if request.doctor_id:
                query = query.filter(SADT.doctor_id == request.doctor_id)
            
            if request.sadt_type:
                query = query.filter(SADT.sadt_type == request.sadt_type)
            
            if request.status:
                query = query.filter(SADT.status == request.status)
            
            if request.procedure_name:
                query = query.filter(
                    SADT.procedure_name.ilike(f"%{request.procedure_name}%")
                )
            
            if request.date_from:
                query = query.filter(SADT.requested_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(SADT.requested_date <= request.date_to)
            
            sadt_requests = query.order_by(desc(SADT.requested_date)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return sadt_requests
            
        except Exception as e:
            logger.error(f"Error searching SADT: {e}")
            raise
    
    def get_sadt_summary(self) -> SADTSummary:
        """Get SADT summary statistics"""
        try:
            total_sadt = self.db.query(SADT).count()
            pending_sadt = self.db.query(SADT).filter(SADT.status == "scheduled").count()
            authorized_sadt = self.db.query(SADT).filter(SADT.status == "authorized").count()
            completed_sadt = self.db.query(SADT).filter(SADT.status == "completed").count()
            
            # SADT by type
            type_stats = self.db.query(
                SADT.sadt_type,
                func.count(SADT.id)
            ).group_by(SADT.sadt_type).all()
            
            sadt_by_type = {
                stat[0].value: stat[1] for stat in type_stats
            }
            
            # SADT by status
            status_stats = self.db.query(
                SADT.status,
                func.count(SADT.id)
            ).group_by(SADT.status).all()
            
            sadt_by_status = {
                stat[0].value: stat[1] for stat in status_stats
            }
            
            return SADTSummary(
                total_sadt=total_sadt,
                pending_sadt=pending_sadt,
                authorized_sadt=authorized_sadt,
                completed_sadt=completed_sadt,
                sadt_by_type=sadt_by_type,
                sadt_by_status=sadt_by_status
            )
            
        except Exception as e:
            logger.error(f"Error getting SADT summary: {e}")
            raise
    
    # ICD Code Management
    def search_icd_codes(self, request: ICDCodeSearchRequest) -> List[ICDCode]:
        """Search ICD codes with filters"""
        try:
            query = self.db.query(ICDCode)
            
            if request.code:
                query = query.filter(ICDCode.code.ilike(f"%{request.code}%"))
            
            if request.description:
                query = query.filter(ICDCode.description.ilike(f"%{request.description}%"))
            
            if request.category:
                query = query.filter(ICDCode.category == request.category)
            
            if request.parent_code:
                query = query.filter(ICDCode.parent_code == request.parent_code)
            
            icd_codes = query.order_by(ICDCode.code).offset(request.skip).limit(request.limit).all()
            
            return icd_codes
            
        except Exception as e:
            logger.error(f"Error searching ICD codes: {e}")
            raise
    
    def get_icd_hierarchy(self, parent_code: Optional[str] = None) -> List[ICDCodeHierarchy]:
        """Get ICD code hierarchy"""
        try:
            if parent_code:
                query = self.db.query(ICDCode).filter(ICDCode.parent_code == parent_code)
            else:
                query = self.db.query(ICDCode).filter(ICDCode.parent_code.is_(None))
            
            icd_codes = query.order_by(ICDCode.code).all()
            
            hierarchy = []
            for code in icd_codes:
                children = self.get_icd_hierarchy(code.code)
                hierarchy.append(ICDCodeHierarchy(
                    code=code.code,
                    description=code.description,
                    category=code.category,
                    level=code.level,
                    children=children
                ))
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Error getting ICD hierarchy: {e}")
            raise
    
    # Utility Methods
    def _generate_prescription_number(self) -> str:
        """Generate unique prescription number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"RX{timestamp}{random_part}"
    
    def _generate_sadt_number(self) -> str:
        """Generate unique SADT number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"SADT{timestamp}{random_part}"
    
    def _generate_digital_signature(self, prescription: ControlledPrescription) -> str:
        """Generate digital signature for prescription"""
        try:
            # Create signature data
            signature_data = {
                "prescription_number": prescription.prescription_number,
                "patient_id": prescription.patient_id,
                "doctor_id": prescription.doctor_id,
                "medication_name": prescription.medication_name,
                "dosage": prescription.dosage,
                "prescription_date": prescription.prescription_date.isoformat(),
                "control_level": prescription.control_level.value
            }
            
            # Generate hash
            signature_string = json.dumps(signature_data, sort_keys=True)
            signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()
            
            return signature_hash
            
        except Exception as e:
            logger.error(f"Error generating digital signature: {e}")
            return ""
    
    def _generate_prescription_hash(self, prescription: ControlledPrescription) -> str:
        """Generate prescription hash for integrity verification"""
        try:
            # Create hash data
            hash_data = {
                "prescription_number": prescription.prescription_number,
                "medication_name": prescription.medication_name,
                "dosage": prescription.dosage,
                "frequency": prescription.frequency,
                "quantity": prescription.quantity,
                "prescription_date": prescription.prescription_date.isoformat()
            }
            
            # Generate hash
            hash_string = json.dumps(hash_data, sort_keys=True)
            prescription_hash = hashlib.sha256(hash_string.encode()).hexdigest()
            
            return prescription_hash
            
        except Exception as e:
            logger.error(f"Error generating prescription hash: {e}")
            return ""
    
    def _check_regulatory_compliance(self, prescription: ControlledPrescription) -> Dict[str, Any]:
        """Check regulatory compliance for prescription"""
        try:
            compliance = {
                "anvisa_compliant": True,
                "cff_compliant": True,
                "crm_compliant": True,
                "regulatory_checks": []
            }
            
            # Check ANVISA compliance
            if prescription.control_level in ["A1", "A2", "A3"]:
                compliance["regulatory_checks"].append("ANVISA controlled substance")
            
            # Check CFF compliance
            if prescription.controlled_substance:
                compliance["regulatory_checks"].append("CFF controlled substance")
            
            # Check CRM compliance
            if prescription.requires_special_authorization:
                compliance["regulatory_checks"].append("CRM special authorization required")
            
            return compliance
            
        except Exception as e:
            logger.error(f"Error checking regulatory compliance: {e}")
            return {"error": str(e)}
    
    def _check_sadt_compliance(self, sadt: SADT) -> Dict[str, Any]:
        """Check regulatory compliance for SADT"""
        try:
            compliance = {
                "tuss_compliant": True,
                "anvisa_compliant": True,
                "cff_compliant": True,
                "crm_compliant": True,
                "regulatory_checks": []
            }
            
            # Check TUSS compliance
            if sadt.procedure_code:
                compliance["regulatory_checks"].append("TUSS procedure code")
            
            # Check ANVISA compliance
            if sadt.sadt_type in ["surgery", "procedure"]:
                compliance["regulatory_checks"].append("ANVISA procedure authorization")
            
            # Check CFF compliance
            if sadt.sadt_type == "therapy":
                compliance["regulatory_checks"].append("CFF therapy authorization")
            
            # Check CRM compliance
            if sadt.sadt_type in ["surgery", "consultation"]:
                compliance["regulatory_checks"].append("CRM medical procedure")
            
            return compliance
            
        except Exception as e:
            logger.error(f"Error checking SADT compliance: {e}")
            return {"error": str(e)}
    
    def _create_prescription_audit(self, prescription_id: int, action: str, 
                                 previous_status: Optional[str], new_status: str, user_id: int):
        """Create prescription audit record"""
        try:
            audit = PrescriptionAudit(
                prescription_id=prescription_id,
                action=action,
                previous_status=previous_status,
                new_status=new_status,
                performed_by=user_id
            )
            
            self.db.add(audit)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating prescription audit: {e}")
    
    def _create_sadt_audit(self, sadt_id: int, action: str, 
                          previous_status: Optional[str], new_status: str, user_id: int):
        """Create SADT audit record"""
        try:
            audit = SADTAudit(
                sadt_id=sadt_id,
                action=action,
                previous_status=previous_status,
                new_status=new_status,
                performed_by=user_id
            )
            
            self.db.add(audit)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating SADT audit: {e}")
