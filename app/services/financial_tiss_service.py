import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from decimal import Decimal
import uuid
import xml.etree.ElementTree as ET
import requests

from app.models.financial_tiss import (
    TISSCode, TISSProcedure, Invoice, Payment, FinancialReport,
    TISSIntegration, TISSSubmission, HealthPlanFinancial
)
from app.schemas.financial_tiss import (
    TISSCodeSearchRequest, TISSProcedureSearchRequest, InvoiceSearchRequest,
    PaymentSearchRequest, TISSSubmissionRequest, FinancialSummary,
    TISSDashboardSummary
)

logger = logging.getLogger(__name__)

class FinancialTISSService:
    """Service for Financial and TISS management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # TISS Code Management
    def create_tiss_code(self, tiss_code_data: dict) -> TISSCode:
        """Create a new TISS code"""
        try:
            tiss_code = TISSCode(**tiss_code_data)
            self.db.add(tiss_code)
            self.db.commit()
            self.db.refresh(tiss_code)
            return tiss_code
        except Exception as e:
            logger.error(f"Error creating TISS code: {e}")
            raise
    
    def search_tiss_codes(self, request: TISSCodeSearchRequest) -> List[TISSCode]:
        """Search TISS codes with filters"""
        try:
            query = self.db.query(TISSCode)
            
            if request.code:
                query = query.filter(TISSCode.code.ilike(f"%{request.code}%"))
            
            if request.description:
                query = query.filter(TISSCode.description.ilike(f"%{request.description}%"))
            
            if request.category:
                query = query.filter(TISSCode.category == request.category)
            
            if request.tiss_version:
                query = query.filter(TISSCode.tiss_version == request.tiss_version)
            
            if request.is_active is not None:
                query = query.filter(TISSCode.is_active == request.is_active)
            
            tiss_codes = query.order_by(TISSCode.code).offset(request.skip).limit(request.limit).all()
            return tiss_codes
        except Exception as e:
            logger.error(f"Error searching TISS codes: {e}")
            raise
    
    # TISS Procedure Management
    def create_tiss_procedure(self, procedure_data: dict, user_id: int) -> TISSProcedure:
        """Create a new TISS procedure"""
        try:
            # Generate procedure number
            procedure_number = self._generate_procedure_number()
            
            # Calculate final value
            base_value = Decimal(str(procedure_data['base_value']))
            discount_percentage = procedure_data.get('discount_percentage', 0.0)
            discount_amount = base_value * (Decimal(str(discount_percentage)) / 100)
            final_value = base_value - discount_amount
            
            # Create procedure
            procedure = TISSProcedure(
                procedure_number=procedure_number,
                base_value=base_value,
                discount_amount=discount_amount,
                final_value=final_value,
                **procedure_data,
                created_by=user_id
            )
            
            self.db.add(procedure)
            self.db.commit()
            self.db.refresh(procedure)
            
            return procedure
        except Exception as e:
            logger.error(f"Error creating TISS procedure: {e}")
            raise
    
    def search_tiss_procedures(self, request: TISSProcedureSearchRequest) -> List[TISSProcedure]:
        """Search TISS procedures with filters"""
        try:
            query = self.db.query(TISSProcedure)
            
            if request.patient_id:
                query = query.filter(TISSProcedure.patient_id == request.patient_id)
            
            if request.doctor_id:
                query = query.filter(TISSProcedure.doctor_id == request.doctor_id)
            
            if request.tiss_code_id:
                query = query.filter(TISSProcedure.tiss_code_id == request.tiss_code_id)
            
            if request.status:
                query = query.filter(TISSProcedure.status == request.status)
            
            if request.payment_status:
                query = query.filter(TISSProcedure.payment_status == request.payment_status)
            
            if request.date_from:
                query = query.filter(TISSProcedure.procedure_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(TISSProcedure.procedure_date <= request.date_to)
            
            procedures = query.order_by(desc(TISSProcedure.procedure_date)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return procedures
        except Exception as e:
            logger.error(f"Error searching TISS procedures: {e}")
            raise
    
    # Invoice Management
    def create_invoice(self, invoice_data: dict, user_id: int) -> Invoice:
        """Create a new invoice"""
        try:
            # Generate invoice number
            invoice_number = self._generate_invoice_number()
            
            # Calculate total amount
            subtotal = Decimal(str(invoice_data['subtotal']))
            discount_amount = Decimal(str(invoice_data.get('discount_amount', 0)))
            tax_amount = Decimal(str(invoice_data.get('tax_amount', 0)))
            total_amount = subtotal - discount_amount + tax_amount
            
            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                subtotal=subtotal,
                total_amount=total_amount,
                **invoice_data,
                created_by=user_id
            )
            
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            
            return invoice
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            raise
    
    def search_invoices(self, request: InvoiceSearchRequest) -> List[Invoice]:
        """Search invoices with filters"""
        try:
            query = self.db.query(Invoice)
            
            if request.patient_id:
                query = query.filter(Invoice.patient_id == request.patient_id)
            
            if request.health_plan_id:
                query = query.filter(Invoice.health_plan_id == request.health_plan_id)
            
            if request.status:
                query = query.filter(Invoice.status == request.status)
            
            if request.payment_status:
                query = query.filter(Invoice.payment_status == request.payment_status)
            
            if request.date_from:
                query = query.filter(Invoice.invoice_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(Invoice.invoice_date <= request.date_to)
            
            invoices = query.order_by(desc(Invoice.invoice_date)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return invoices
        except Exception as e:
            logger.error(f"Error searching invoices: {e}")
            raise
    
    # Payment Management
    def create_payment(self, payment_data: dict, user_id: int) -> Payment:
        """Create a new payment"""
        try:
            # Generate payment number
            payment_number = self._generate_payment_number()
            
            # Create payment
            payment = Payment(
                payment_number=payment_number,
                **payment_data,
                created_by=user_id
            )
            
            self.db.add(payment)
            
            # Update invoice payment status
            invoice = self.db.query(Invoice).filter(
                Invoice.id == payment_data['invoice_id']
            ).first()
            
            if invoice:
                invoice.paid_amount += payment.amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.payment_status = "paid"
                    invoice.status = "paid"
                else:
                    invoice.payment_status = "processing"
            
            self.db.commit()
            self.db.refresh(payment)
            
            return payment
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise
    
    def search_payments(self, request: PaymentSearchRequest) -> List[Payment]:
        """Search payments with filters"""
        try:
            query = self.db.query(Payment)
            
            if request.patient_id:
                query = query.filter(Payment.patient_id == request.patient_id)
            
            if request.invoice_id:
                query = query.filter(Payment.invoice_id == request.invoice_id)
            
            if request.status:
                query = query.filter(Payment.status == request.status)
            
            if request.payment_method:
                query = query.filter(Payment.payment_method == request.payment_method)
            
            if request.date_from:
                query = query.filter(Payment.payment_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(Payment.payment_date <= request.date_to)
            
            payments = query.order_by(desc(Payment.payment_date)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return payments
        except Exception as e:
            logger.error(f"Error searching payments: {e}")
            raise
    
    # Financial Summary
    def get_financial_summary(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> FinancialSummary:
        """Get financial summary statistics"""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Convert dates to datetime for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Get procedures in date range
            procedures_query = self.db.query(TISSProcedure).filter(
                TISSProcedure.procedure_date >= start_datetime,
                TISSProcedure.procedure_date <= end_datetime
            )
            
            total_procedures = procedures_query.count()
            total_revenue = procedures_query.with_entities(
                func.sum(TISSProcedure.final_value)
            ).scalar() or Decimal('0')
            
            # Get payments in date range
            payments_query = self.db.query(Payment).filter(
                Payment.payment_date >= start_datetime,
                Payment.payment_date <= end_datetime,
                Payment.status == "paid"
            )
            
            total_payments = payments_query.with_entities(
                func.sum(Payment.amount)
            ).scalar() or Decimal('0')
            
            # Calculate outstanding amount
            total_outstanding = total_revenue - total_payments
            
            # Procedures by status
            procedures_by_status = {}
            status_stats = procedures_query.with_entities(
                TISSProcedure.status,
                func.count(TISSProcedure.id)
            ).group_by(TISSProcedure.status).all()
            
            for stat in status_stats:
                procedures_by_status[stat[0].value] = stat[1]
            
            # Revenue by category
            revenue_by_category = {}
            category_stats = procedures_query.join(TISSCode).with_entities(
                TISSCode.category,
                func.sum(TISSProcedure.final_value)
            ).group_by(TISSCode.category).all()
            
            for stat in category_stats:
                revenue_by_category[stat[0].value] = stat[1] or Decimal('0')
            
            # Payments by method
            payments_by_method = {}
            method_stats = payments_query.with_entities(
                Payment.payment_method,
                func.sum(Payment.amount)
            ).group_by(Payment.payment_method).all()
            
            for stat in method_stats:
                payments_by_method[stat[0]] = stat[1] or Decimal('0')
            
            # Outstanding by health plan
            outstanding_by_health_plan = {}
            outstanding_query = self.db.query(TISSProcedure).filter(
                TISSProcedure.payment_status == "pending"
            )
            
            # This would need to be joined with health plans
            # For now, return empty dict
            outstanding_by_health_plan = {}
            
            return FinancialSummary(
                total_procedures=total_procedures,
                total_revenue=total_revenue,
                total_payments=total_payments,
                total_outstanding=total_outstanding,
                procedures_by_status=procedures_by_status,
                revenue_by_category=revenue_by_category,
                payments_by_method=payments_by_method,
                outstanding_by_health_plan=outstanding_by_health_plan
            )
        except Exception as e:
            logger.error(f"Error getting financial summary: {e}")
            raise
    
    # TISS Integration
    def create_tiss_integration(self, integration_data: dict, user_id: int) -> TISSIntegration:
        """Create a new TISS integration"""
        try:
            integration = TISSIntegration(
                **integration_data,
                created_by=user_id
            )
            
            self.db.add(integration)
            self.db.commit()
            self.db.refresh(integration)
            
            return integration
        except Exception as e:
            logger.error(f"Error creating TISS integration: {e}")
            raise
    
    def submit_to_tiss(self, request: TISSSubmissionRequest) -> TISSSubmission:
        """Submit procedure to TISS"""
        try:
            # Get procedure and integration
            procedure = self.db.query(TISSProcedure).filter(
                TISSProcedure.id == request.procedure_id
            ).first()
            
            integration = self.db.query(TISSIntegration).filter(
                TISSIntegration.id == request.integration_id
            ).first()
            
            if not procedure or not integration:
                raise ValueError("Procedure or integration not found")
            
            # Generate submission ID
            submission_id = self._generate_submission_id()
            
            # Generate TISS XML
            tiss_xml = self._generate_tiss_xml(procedure, integration)
            
            # Create submission record
            submission = TISSSubmission(
                submission_id=submission_id,
                integration_id=request.integration_id,
                procedure_id=request.procedure_id,
                submission_date=datetime.utcnow(),
                submission_type=request.submission_type,
                tiss_xml=tiss_xml,
                status="pending"
            )
            
            self.db.add(submission)
            
            # Update procedure
            procedure.tiss_submission_id = submission_id
            procedure.status = "processing"
            
            self.db.commit()
            self.db.refresh(submission)
            
            # Submit to TISS API (async)
            self._submit_to_tiss_api(submission, integration)
            
            return submission
        except Exception as e:
            logger.error(f"Error submitting to TISS: {e}")
            raise
    
    def _submit_to_tiss_api(self, submission: TISSSubmission, integration: TISSIntegration):
        """Submit to TISS API (mock implementation)"""
        try:
            # Mock TISS API submission
            # In real implementation, this would make HTTP request to TISS API
            
            # Simulate API response
            tiss_response = {
                "status": "success",
                "message": "Procedure submitted successfully",
                "tiss_id": f"TISS_{submission.submission_id}",
                "submission_date": datetime.utcnow().isoformat()
            }
            
            # Update submission
            submission.tiss_response = json.dumps(tiss_response)
            submission.tiss_status = "approved"
            submission.tiss_message = tiss_response["message"]
            submission.status = "approved"
            submission.processed_at = datetime.utcnow()
            
            # Update procedure
            procedure = self.db.query(TISSProcedure).filter(
                TISSProcedure.id == submission.procedure_id
            ).first()
            
            if procedure:
                procedure.status = "approved"
                procedure.tiss_response = tiss_response
            
            # Update integration
            integration.last_sync = datetime.utcnow()
            integration.last_success = datetime.utcnow()
            integration.last_error = None
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error submitting to TISS API: {e}")
            
            # Update submission with error
            submission.tiss_status = "rejected"
            submission.tiss_message = str(e)
            submission.status = "rejected"
            submission.error_code = "API_ERROR"
            submission.error_message = str(e)
            
            # Update integration
            integration.last_error = str(e)
            
            self.db.commit()
    
    def get_tiss_dashboard_summary(self) -> TISSDashboardSummary:
        """Get TISS dashboard summary"""
        try:
            # Get submission statistics
            total_submissions = self.db.query(TISSSubmission).count()
            successful_submissions = self.db.query(TISSSubmission).filter(
                TISSSubmission.status == "approved"
            ).count()
            failed_submissions = self.db.query(TISSSubmission).filter(
                TISSSubmission.status == "rejected"
            ).count()
            pending_submissions = self.db.query(TISSSubmission).filter(
                TISSSubmission.status == "pending"
            ).count()
            
            # Submissions by status
            submissions_by_status = {}
            status_stats = self.db.query(
                TISSSubmission.status,
                func.count(TISSSubmission.id)
            ).group_by(TISSSubmission.status).all()
            
            for stat in status_stats:
                submissions_by_status[stat[0].value] = stat[1]
            
            # Recent submissions
            recent_submissions = self.db.query(TISSSubmission).order_by(
                desc(TISSSubmission.submission_date)
            ).limit(10).all()
            
            recent_submissions_data = []
            for submission in recent_submissions:
                recent_submissions_data.append({
                    "id": submission.id,
                    "submission_id": submission.submission_id,
                    "status": submission.status.value,
                    "submission_date": submission.submission_date.isoformat(),
                    "tiss_status": submission.tiss_status,
                    "tiss_message": submission.tiss_message
                })
            
            # Integration status
            integrations = self.db.query(TISSIntegration).filter(
                TISSIntegration.is_active == True
            ).all()
            
            integration_status = {}
            for integration in integrations:
                integration_status[integration.integration_name] = {
                    "is_active": integration.is_active,
                    "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
                    "last_success": integration.last_success.isoformat() if integration.last_success else None,
                    "last_error": integration.last_error
                }
            
            return TISSDashboardSummary(
                total_submissions=total_submissions,
                successful_submissions=successful_submissions,
                failed_submissions=failed_submissions,
                pending_submissions=pending_submissions,
                submissions_by_status=submissions_by_status,
                recent_submissions=recent_submissions_data,
                integration_status=integration_status
            )
        except Exception as e:
            logger.error(f"Error getting TISS dashboard summary: {e}")
            raise
    
    # Utility Methods
    def _generate_procedure_number(self) -> str:
        """Generate unique procedure number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"PROC{timestamp}{random_part}"
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"INV{timestamp}{random_part}"
    
    def _generate_payment_number(self) -> str:
        """Generate unique payment number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"PAY{timestamp}{random_part}"
    
    def _generate_submission_id(self) -> str:
        """Generate unique submission ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"TISS{timestamp}{random_part}"
    
    def _generate_tiss_xml(self, procedure: TISSProcedure, integration: TISSIntegration) -> str:
        """Generate TISS XML for procedure submission"""
        try:
            # Create XML structure
            root = ET.Element("tiss")
            root.set("version", integration.tiss_version)
            
            # Procedure information
            procedure_elem = ET.SubElement(root, "procedure")
            ET.SubElement(procedure_elem, "id").text = procedure.procedure_number
            ET.SubElement(procedure_elem, "date").text = procedure.procedure_date.isoformat()
            ET.SubElement(procedure_elem, "patient_id").text = str(procedure.patient_id)
            ET.SubElement(procedure_elem, "doctor_id").text = str(procedure.doctor_id)
            
            # TISS code information
            tiss_code_elem = ET.SubElement(procedure_elem, "tiss_code")
            ET.SubElement(tiss_code_elem, "code").text = procedure.tiss_code.code
            ET.SubElement(tiss_code_elem, "description").text = procedure.tiss_code.description
            
            # Financial information
            financial_elem = ET.SubElement(procedure_elem, "financial")
            ET.SubElement(financial_elem, "base_value").text = str(procedure.base_value)
            ET.SubElement(financial_elem, "final_value").text = str(procedure.final_value)
            ET.SubElement(financial_elem, "currency").text = procedure.currency
            
            # Medical information
            medical_elem = ET.SubElement(procedure_elem, "medical")
            ET.SubElement(medical_elem, "indication").text = procedure.medical_indication
            if procedure.procedure_description:
                ET.SubElement(medical_elem, "description").text = procedure.procedure_description
            
            # Convert to string
            xml_str = ET.tostring(root, encoding='unicode')
            return xml_str
            
        except Exception as e:
            logger.error(f"Error generating TISS XML: {e}")
            return ""
