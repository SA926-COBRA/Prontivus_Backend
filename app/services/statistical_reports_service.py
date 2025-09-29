"""
Statistical Reports Service
Comprehensive analytics and KPIs for clinic operations
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.statistical_reports import (
    StatisticalReport, ReportType, ReportStatus
)
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.financial import Billing, BillingPayment
from app.models.telemedicine import TelemedicineSession
from app.models.ai_integration import AIAnalysisSession

logger = logging.getLogger(__name__)


class StatisticalReportsService:
    def __init__(self, db: Session):
        self.db = db
        self.reports_storage_path = os.getenv("REPORTS_STORAGE_PATH", "/tmp/reports")
        os.makedirs(self.reports_storage_path, exist_ok=True)

    def create_report(self, report_data: dict, user_id: int) -> StatisticalReport:
        """Create a new statistical report"""
        try:
            report_dict = report_data.copy()
            report_dict['generated_by'] = user_id
            report_dict['status'] = ReportStatus.DRAFT
            
            report = StatisticalReport(**report_dict)
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            return report
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating statistical report: {e}")
            raise

    def get_reports(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[StatisticalReport]:
        """Get statistical reports for a tenant"""
        reports = self.db.query(StatisticalReport).filter(
            StatisticalReport.tenant_id == tenant_id
        ).order_by(desc(StatisticalReport.created_at)).offset(skip).limit(limit).all()
        
        return reports

    def get_dashboard_metrics(self, tenant_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            # Consultation metrics
            total_consultations = self.db.query(Appointment).filter(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.appointment_date >= start_date,
                    Appointment.appointment_date <= end_date
                )
            ).count()
            
            completed_consultations = self.db.query(Appointment).filter(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.appointment_date >= start_date,
                    Appointment.appointment_date <= end_date,
                    Appointment.status == 'completed'
                )
            ).count()
            
            # Prescription metrics
            total_prescriptions = self.db.query(Prescription).filter(
                and_(
                    Prescription.tenant_id == tenant_id,
                    Prescription.created_at >= datetime.combine(start_date, datetime.min.time()),
                    Prescription.created_at <= datetime.combine(end_date, datetime.max.time())
                )
            ).count()
            
            # Financial metrics
            total_billed = self.db.query(func.sum(Billing.total_amount)).filter(
                and_(
                    Billing.tenant_id == tenant_id,
                    Billing.billing_date >= start_date,
                    Billing.billing_date <= end_date
                )
            ).scalar() or 0
            
            total_paid = self.db.query(func.sum(BillingPayment.amount)).filter(
                and_(
                    BillingPayment.tenant_id == tenant_id,
                    BillingPayment.payment_date >= start_date,
                    BillingPayment.payment_date <= end_date
                )
            ).scalar() or 0
            
            return {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_consultations": total_consultations,
                "completed_consultations": completed_consultations,
                "consultation_success_rate": (completed_consultations / total_consultations * 100) if total_consultations > 0 else 0,
                "total_prescriptions": total_prescriptions,
                "total_billed": float(total_billed),
                "total_paid": float(total_paid),
                "payment_rate": (total_paid / total_billed * 100) if total_billed > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            raise

    async def generate_report(self, tenant_id: int, report_id: int, user_id: int) -> Dict[str, Any]:
        """Generate a statistical report"""
        try:
            report = self.db.query(StatisticalReport).filter(
                and_(
                    StatisticalReport.tenant_id == tenant_id,
                    StatisticalReport.id == report_id
                )
            ).first()
            
            if not report:
                return {"success": False, "error": "Report not found"}
            
            report.status = ReportStatus.GENERATING
            self.db.commit()
            
            # Generate simple text report
            filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = os.path.join(self.reports_storage_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"RELATÓRIO - {report.report_name}\n")
                f.write(f"Tipo: {report.report_type.value}\n")
                f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Descrição: {report.description or 'N/A'}\n")
            
            report.status = ReportStatus.COMPLETED
            report.generated_at = datetime.utcnow()
            report.file_path = file_path
            report.file_size = os.path.getsize(file_path)
            self.db.commit()
            
            return {
                "success": True,
                "file_path": file_path,
                "file_size": report.file_size,
                "message": "Report generated successfully"
            }
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"success": False, "error": str(e)}