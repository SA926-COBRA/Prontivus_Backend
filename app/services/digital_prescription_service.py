"""
Digital Prescription Service
Service layer for digital prescription with ICP-Brasil signature
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from cryptography.fernet import Fernet
import base64
import os
import hashlib

from app.models.digital_prescription import (
    DigitalPrescription, PrescriptionMedication, PrescriptionVerification,
    PrescriptionConfiguration, PrescriptionTemplate, PrescriptionAnalytics,
    PrescriptionType, PrescriptionStatus, SignatureType
)
from app.schemas.digital_prescription import (
    DigitalPrescriptionCreate, DigitalPrescriptionUpdate,
    PrescriptionMedicationCreate, PrescriptionConfigurationCreate, PrescriptionConfigurationUpdate,
    PrescriptionTemplateCreate, PrescriptionTemplateUpdate,
    PrescriptionSignRequest, PrescriptionSignResponse,
    PrescriptionDeliveryRequest, PrescriptionDeliveryResponse,
    PrescriptionVerificationRequest, PrescriptionVerificationResponse,
    PrescriptionDashboardResponse, PrescriptionSummary, PrescriptionsResponse
)

logger = logging.getLogger(__name__)


class PrescriptionCryptoService:
    """Service for encrypting/decrypting prescription data"""
    
    def __init__(self):
        self.key = os.getenv('PRESCRIPTION_ENCRYPTION_KEY', Fernet.generate_key())
        if isinstance(self.key, str):
            self.key = self.key.encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt prescription data: {e}")
            return ""


class PrescriptionService:
    """Main service for digital prescription operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crypto = PrescriptionCryptoService()
    
    def create_prescription(self, tenant_id: int, prescription_data: DigitalPrescriptionCreate) -> DigitalPrescription:
        """Create a new digital prescription"""
        try:
            # Generate unique prescription ID
            prescription_id = f"RX_{uuid.uuid4().hex[:12].upper()}"
            
            prescription_dict = prescription_data.dict(exclude={'medications'})
            prescription_dict.update({
                'tenant_id': tenant_id,
                'prescription_id': prescription_id,
                'status': PrescriptionStatus.DRAFT,
                'delivery_status': 'pending',
                'is_valid': True
            })
            
            prescription = DigitalPrescription(**prescription_dict)
            self.db.add(prescription)
            self.db.flush()  # Get the ID
            
            # Add medications
            for med_data in prescription_data.medications:
                medication = PrescriptionMedication(
                    prescription_id=prescription.id,
                    **med_data.dict()
                )
                self.db.add(medication)
            
            self.db.commit()
            self.db.refresh(prescription)
            
            logger.info(f"Created digital prescription: {prescription_id}")
            return prescription
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create digital prescription: {e}")
            raise
    
    def get_prescription(self, prescription_id: str) -> Optional[DigitalPrescription]:
        """Get prescription by prescription ID"""
        return self.db.query(DigitalPrescription).filter(
            DigitalPrescription.prescription_id == prescription_id
        ).first()
    
    def get_prescriptions(self, tenant_id: int, status: Optional[str] = None,
                         doctor_id: Optional[int] = None, patient_id: Optional[int] = None,
                         page: int = 1, page_size: int = 20) -> PrescriptionsResponse:
        """Get prescriptions with pagination"""
        try:
            query = self.db.query(DigitalPrescription).filter(
                DigitalPrescription.tenant_id == tenant_id
            )
            
            if status:
                query = query.filter(DigitalPrescription.status == status)
            if doctor_id:
                query = query.filter(DigitalPrescription.doctor_id == doctor_id)
            if patient_id:
                query = query.filter(DigitalPrescription.patient_id == patient_id)
            
            total_count = query.count()
            offset = (page - 1) * page_size
            prescriptions = query.order_by(desc(DigitalPrescription.created_at)).offset(offset).limit(page_size).all()
            
            prescription_summaries = []
            for prescription in prescriptions:
                doctor_name = f"Dr. User {prescription.doctor_id}"
                patient_name = f"Patient {prescription.patient_id}"
                
                # Count medications
                medication_count = self.db.query(PrescriptionMedication).filter(
                    PrescriptionMedication.prescription_id == prescription.id
                ).count()
                
                prescription_summaries.append(PrescriptionSummary(
                    id=prescription.id,
                    prescription_id=prescription.prescription_id,
                    doctor_name=doctor_name,
                    patient_name=patient_name,
                    prescription_type=prescription.prescription_type.value,
                    status=prescription.status.value,
                    medication_count=medication_count,
                    created_at=prescription.created_at,
                    signed_at=prescription.signed_at,
                    delivered_at=prescription.delivery_timestamp,
                    is_valid=prescription.is_valid
                ))
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return PrescriptionsResponse(
                prescriptions=prescription_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            logger.error(f"Failed to get prescriptions: {e}")
            raise
    
    def sign_prescription(self, prescription_id: str, sign_request: PrescriptionSignRequest) -> PrescriptionSignResponse:
        """Sign a digital prescription"""
        try:
            prescription = self.get_prescription(prescription_id)
            if not prescription:
                return PrescriptionSignResponse(
                    success=False,
                    prescription_id=prescription_id,
                    message="Prescription not found"
                )
            
            if prescription.status != PrescriptionStatus.DRAFT:
                return PrescriptionSignResponse(
                    success=False,
                    prescription_id=prescription_id,
                    message="Prescription cannot be signed in current status"
                )
            
            # In a real implementation, this would perform actual digital signature
            # For now, simulate the signing process
            signature_hash = hashlib.sha256(f"{prescription_id}_{datetime.now()}".encode()).hexdigest()
            
            prescription.status = PrescriptionStatus.SIGNED
            prescription.signature_type = sign_request.signature_type
            prescription.signature_hash = signature_hash
            prescription.signature_timestamp = datetime.now()
            prescription.signed_at = datetime.now()
            
            # Generate PDF path (simulated)
            pdf_path = f"/prescriptions/{prescription_id}.pdf"
            prescription.pdf_path = pdf_path
            prescription.pdf_hash = hashlib.sha256(pdf_path.encode()).hexdigest()
            
            # Generate QR code URL (simulated)
            qr_code_url = f"https://prescriptions.prontivus.com/verify/{prescription_id}"
            prescription.qr_code_url = qr_code_url
            
            self.db.commit()
            
            logger.info(f"Signed digital prescription: {prescription_id}")
            return PrescriptionSignResponse(
                success=True,
                prescription_id=prescription_id,
                signature_hash=signature_hash,
                pdf_path=pdf_path,
                qr_code_url=qr_code_url,
                message="Prescription signed successfully"
            )
        except Exception as e:
            logger.error(f"Failed to sign prescription: {e}")
            return PrescriptionSignResponse(
                success=False,
                prescription_id=prescription_id,
                message=f"Failed to sign prescription: {str(e)}"
            )
    
    def deliver_prescription(self, prescription_id: str, delivery_request: PrescriptionDeliveryRequest) -> PrescriptionDeliveryResponse:
        """Deliver a prescription to patient"""
        try:
            prescription = self.get_prescription(prescription_id)
            if not prescription:
                return PrescriptionDeliveryResponse(
                    success=False,
                    prescription_id=prescription_id,
                    message="Prescription not found"
                )
            
            if prescription.status != PrescriptionStatus.SIGNED:
                return PrescriptionDeliveryResponse(
                    success=False,
                    prescription_id=prescription_id,
                    message="Prescription must be signed before delivery"
                )
            
            # Update delivery information
            prescription.delivery_method = delivery_request.delivery_method
            prescription.delivery_recipient = delivery_request.delivery_recipient
            prescription.delivery_status = "sent"
            prescription.delivery_timestamp = datetime.now()
            prescription.status = PrescriptionStatus.DELIVERED
            
            self.db.commit()
            
            logger.info(f"Delivered prescription: {prescription_id}")
            return PrescriptionDeliveryResponse(
                success=True,
                prescription_id=prescription_id,
                delivery_status="sent",
                delivery_timestamp=prescription.delivery_timestamp,
                message="Prescription delivered successfully"
            )
        except Exception as e:
            logger.error(f"Failed to deliver prescription: {e}")
            return PrescriptionDeliveryResponse(
                success=False,
                prescription_id=prescription_id,
                message=f"Failed to deliver prescription: {str(e)}"
            )
    
    def verify_prescription(self, verification_request: PrescriptionVerificationRequest) -> PrescriptionVerificationResponse:
        """Verify a prescription using QR code"""
        try:
            verification = self.db.query(PrescriptionVerification).filter(
                PrescriptionVerification.verification_token == verification_request.verification_token
            ).first()
            
            if not verification:
                return PrescriptionVerificationResponse(
                    success=False,
                    is_valid=False,
                    error_message="Invalid verification token"
                )
            
            prescription = self.get_prescription_by_id(verification.prescription_id)
            if not prescription:
                return PrescriptionVerificationResponse(
                    success=False,
                    is_valid=False,
                    error_message="Prescription not found"
                )
            
            # Update verification record
            verification.requested_at = datetime.now()
            verification.ip_address = verification_request.ip_address
            verification.user_agent = verification_request.user_agent
            verification.is_valid = prescription.is_valid and prescription.status == PrescriptionStatus.SIGNED
            verification.verification_timestamp = datetime.now()
            
            self.db.commit()
            
            doctor_name = f"Dr. User {prescription.doctor_id}"
            patient_name = f"Patient {prescription.patient_id}"
            
            return PrescriptionVerificationResponse(
                success=True,
                is_valid=verification.is_valid,
                prescription_id=prescription.prescription_id,
                doctor_name=doctor_name,
                patient_name=patient_name,
                prescription_date=prescription.created_at,
                signature_valid=prescription.signature_hash is not None,
                verification_details={
                    "prescription_type": prescription.prescription_type.value,
                    "signature_timestamp": prescription.signature_timestamp.isoformat() if prescription.signature_timestamp else None,
                    "delivery_status": prescription.delivery_status
                }
            )
        except Exception as e:
            logger.error(f"Failed to verify prescription: {e}")
            return PrescriptionVerificationResponse(
                success=False,
                is_valid=False,
                error_message=f"Verification failed: {str(e)}"
            )
    
    def get_prescription_by_id(self, prescription_id: int) -> Optional[DigitalPrescription]:
        """Get prescription by ID"""
        return self.db.query(DigitalPrescription).filter(
            DigitalPrescription.id == prescription_id
        ).first()
    
    def get_configuration(self, tenant_id: int) -> Optional[PrescriptionConfiguration]:
        """Get prescription configuration for a tenant"""
        return self.db.query(PrescriptionConfiguration).filter(
            PrescriptionConfiguration.tenant_id == tenant_id
        ).first()
    
    def create_or_update_configuration(self, tenant_id: int, 
                                     config_data: PrescriptionConfigurationCreate) -> PrescriptionConfiguration:
        """Create or update prescription configuration"""
        try:
            existing_config = self.get_configuration(tenant_id)
            
            if existing_config:
                update_dict = config_data.dict(exclude_unset=True)
                
                # Encrypt sensitive data
                if 'certificate_password' in update_dict and update_dict['certificate_password']:
                    update_dict['certificate_password'] = self.crypto.encrypt(update_dict['certificate_password'])
                if 'pharmacy_api_key' in update_dict and update_dict['pharmacy_api_key']:
                    update_dict['pharmacy_api_key'] = self.crypto.encrypt(update_dict['pharmacy_api_key'])
                
                for field, value in update_dict.items():
                    if hasattr(existing_config, field) and value is not None:
                        setattr(existing_config, field, value)
                
                self.db.commit()
                self.db.refresh(existing_config)
                return existing_config
            else:
                config_dict = config_data.dict()
                config_dict['tenant_id'] = tenant_id
                
                # Encrypt sensitive data
                if config_dict.get('certificate_password'):
                    config_dict['certificate_password'] = self.crypto.encrypt(config_dict['certificate_password'])
                if config_dict.get('pharmacy_api_key'):
                    config_dict['pharmacy_api_key'] = self.crypto.encrypt(config_dict['pharmacy_api_key'])
                
                configuration = PrescriptionConfiguration(**config_dict)
                self.db.add(configuration)
                self.db.commit()
                self.db.refresh(configuration)
                return configuration
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update prescription configuration: {e}")
            raise
    
    def get_dashboard_data(self, tenant_id: int) -> PrescriptionDashboardResponse:
        """Get prescription dashboard data"""
        try:
            # Get counts
            total_prescriptions = self.db.query(DigitalPrescription).filter(
                DigitalPrescription.tenant_id == tenant_id
            ).count()
            
            signed_prescriptions = self.db.query(DigitalPrescription).filter(
                and_(
                    DigitalPrescription.tenant_id == tenant_id,
                    DigitalPrescription.status == PrescriptionStatus.SIGNED
                )
            ).count()
            
            pending_signatures = self.db.query(DigitalPrescription).filter(
                and_(
                    DigitalPrescription.tenant_id == tenant_id,
                    DigitalPrescription.status == PrescriptionStatus.DRAFT
                )
            ).count()
            
            # Delivered today
            today = datetime.now().date()
            delivered_today = self.db.query(DigitalPrescription).filter(
                and_(
                    DigitalPrescription.tenant_id == tenant_id,
                    DigitalPrescription.status == PrescriptionStatus.DELIVERED,
                    DigitalPrescription.delivery_timestamp >= today
                )
            ).count()
            
            # This month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            prescriptions_this_month = self.db.query(DigitalPrescription).filter(
                and_(
                    DigitalPrescription.tenant_id == tenant_id,
                    DigitalPrescription.created_at >= month_start
                )
            ).count()
            
            # Average per day (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            prescriptions_last_30_days = self.db.query(DigitalPrescription).filter(
                and_(
                    DigitalPrescription.tenant_id == tenant_id,
                    DigitalPrescription.created_at >= thirty_days_ago
                )
            ).count()
            average_prescriptions_per_day = prescriptions_last_30_days / 30
            
            # Most prescribed medications (simplified)
            most_prescribed_medications = []  # In production, this would be calculated from actual data
            
            # Prescriptions by type
            prescriptions_by_type = {}
            for prescription_type in PrescriptionType:
                count = self.db.query(DigitalPrescription).filter(
                    and_(
                        DigitalPrescription.tenant_id == tenant_id,
                        DigitalPrescription.prescription_type == prescription_type
                    )
                ).count()
                prescriptions_by_type[prescription_type.value] = count
            
            # Delivery methods breakdown
            delivery_methods_breakdown = {
                "email": 0,
                "whatsapp": 0,
                "portal": 0,
                "link": 0
            }
            
            # Recent prescriptions
            recent_prescriptions = self.db.query(DigitalPrescription).filter(
                DigitalPrescription.tenant_id == tenant_id
            ).order_by(desc(DigitalPrescription.created_at)).limit(5).all()
            
            recent_prescriptions_data = []
            for prescription in recent_prescriptions:
                recent_prescriptions_data.append({
                    "id": prescription.id,
                    "prescription_id": prescription.prescription_id,
                    "status": prescription.status.value,
                    "created_at": prescription.created_at.isoformat(),
                    "medication_count": 0  # Simplified
                })
            
            return PrescriptionDashboardResponse(
                total_prescriptions=total_prescriptions,
                signed_prescriptions=signed_prescriptions,
                pending_signatures=pending_signatures,
                delivered_today=delivered_today,
                prescriptions_this_month=prescriptions_this_month,
                average_prescriptions_per_day=round(average_prescriptions_per_day, 2),
                most_prescribed_medications=most_prescribed_medications,
                prescriptions_by_type=prescriptions_by_type,
                delivery_methods_breakdown=delivery_methods_breakdown,
                recent_prescriptions=recent_prescriptions_data
            )
        except Exception as e:
            logger.error(f"Failed to get prescription dashboard data: {e}")
            raise
