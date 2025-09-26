from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging

from app.database.database import get_db
from app.models.reports import GeneratedReport, ReportTemplate, ReportAccessLog
from app.models.user import User
from app.schemas.reports import (
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplate as ReportTemplateSchema,
    GeneratedReportCreate, GeneratedReportUpdate, GeneratedReport as GeneratedReportSchema,
    ReportGenerationRequest, BulkReportGenerationRequest,
    ReportAnalytics, ReportUsageStats, ReportDashboardStats,
    ReportValidationRequest, ReportValidationResponse,
    ReportExportRequest, ReportExportResponse
)
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.core.exceptions import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Report Templates endpoints
@router.get("/templates", response_model=List[ReportTemplateSchema], summary="Get all report templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all report templates with filtering options"""
    query = db.query(ReportTemplate)
    
    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)
    
    if is_active is not None:
        query = query.filter(ReportTemplate.is_active == is_active)
    
    templates = query.offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=ReportTemplateSchema, summary="Get report template by ID")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report template by ID"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    return template

@router.post("/templates", response_model=ReportTemplateSchema, status_code=status.HTTP_201_CREATED, summary="Create new report template")
async def create_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report template"""
    template = ReportTemplate(
        **template_data.dict(),
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.put("/templates/{template_id}", response_model=ReportTemplateSchema, summary="Update report template")
async def update_template(
    template_id: int,
    template_data: ReportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report template"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    
    # Check if user can modify this template
    if template.is_system_template and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify system templates"
        )
    
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}", summary="Delete report template")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report template"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    
    # Check if user can delete this template
    if template.is_system_template and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete system templates"
        )
    
    # Soft delete by setting is_active to False
    template.is_active = False
    db.commit()
    return {"message": "Report template deactivated successfully"}

# Report Generation endpoints
@router.post("/generate", response_model=GeneratedReportSchema, status_code=status.HTTP_201_CREATED, summary="Generate a new report")
async def generate_report(
    request: ReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new report"""
    try:
        report_service = ReportService(db)
        report = report_service.generate_report(request, current_user.id)
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.post("/generate/bulk", response_model=List[GeneratedReportSchema], status_code=status.HTTP_201_CREATED, summary="Generate multiple reports")
async def generate_bulk_reports(
    request: BulkReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate multiple reports in bulk"""
    try:
        report_service = ReportService(db)
        reports = []
        
        for report_request in request.reports:
            try:
                report = report_service.generate_report(report_request, current_user.id)
                reports.append(report)
            except Exception as e:
                logger.error(f"Error generating report in bulk: {e}")
                # Continue with other reports even if one fails
        
        return reports
    except Exception as e:
        logger.error(f"Error in bulk report generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk reports: {str(e)}"
        )

# Generated Reports endpoints
@router.get("/reports", response_model=List[GeneratedReportSchema], summary="Get user's generated reports")
async def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    report_format: Optional[str] = Query(None)
):
    """Get user's generated reports with filtering options"""
    query = db.query(GeneratedReport).filter(GeneratedReport.created_by == current_user.id)
    
    if status:
        query = query.filter(GeneratedReport.status == status)
    
    if report_type:
        query = query.filter(GeneratedReport.report_type == report_type)
    
    if report_format:
        query = query.filter(GeneratedReport.report_format == report_format)
    
    reports = query.order_by(GeneratedReport.created_at.desc()).offset(skip).limit(limit).all()
    return reports

@router.get("/reports/{report_id}", response_model=GeneratedReportSchema, summary="Get generated report by ID")
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific generated report by ID"""
    report_service = ReportService(db)
    report = report_service.get_report(report_id, current_user.id)
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    # Log access
    report_service.log_access(report_id, current_user.id, "view")
    
    return report

@router.get("/reports/{report_id}/download", summary="Download generated report")
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a generated report file"""
    report_service = ReportService(db)
    report = report_service.get_report(report_id, current_user.id)
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    if report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download"
        )
    
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    # Log download access
    report_service.log_access(report_id, current_user.id, "download")
    
    # Determine media type based on file extension
    file_extension = os.path.splitext(report.file_path)[1].lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv',
        '.html': 'text/html'
    }
    
    media_type = media_types.get(file_extension, 'application/octet-stream')
    
    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type=media_type
    )

@router.delete("/reports/{report_id}", summary="Delete generated report")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a generated report"""
    report_service = ReportService(db)
    success = report_service.delete_report(report_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    return {"message": "Report deleted successfully"}

# Report Validation endpoint
@router.post("/validate", response_model=ReportValidationResponse, summary="Validate report parameters")
async def validate_report(
    request: ReportValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate report parameters before generation"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    
    # Basic validation logic
    errors = []
    warnings = []
    
    # Check if template is active
    if not template.is_active:
        errors.append("Template is not active")
    
    # Check permissions
    if template.requires_permission and not current_user.is_superuser:
        errors.append("Insufficient permissions for this template")
    
    # Validate date range if provided
    if request.parameters:
        date_start = request.parameters.get('date_range_start')
        date_end = request.parameters.get('date_range_end')
        
        if date_start and date_end:
            try:
                start_date = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
                
                if start_date > end_date:
                    errors.append("Start date cannot be after end date")
                
                if (end_date - start_date).days > 365:
                    warnings.append("Date range exceeds 1 year, generation may take longer")
            except ValueError:
                errors.append("Invalid date format")
    
    # Estimate generation time and file size (mock values)
    estimated_time = 30  # seconds
    estimated_size = 1.5  # MB
    
    return ReportValidationResponse(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        estimated_generation_time_seconds=estimated_time,
        estimated_file_size_mb=estimated_size
    )

# Analytics endpoints
@router.get("/analytics", response_model=ReportAnalytics, summary="Get report analytics")
async def get_report_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get report analytics and statistics"""
    # This would contain actual analytics queries
    # For now, returning mock data
    
    analytics = ReportAnalytics(
        total_reports_generated=0,
        reports_by_type={},
        reports_by_format={},
        most_used_templates=[],
        generation_success_rate=0.0,
        average_generation_time_seconds=0.0,
        total_downloads=0,
        reports_generated_last_30_days=0
    )
    
    return analytics

@router.get("/dashboard", response_model=ReportDashboardStats, summary="Get report dashboard statistics")
async def get_report_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report dashboard statistics"""
    # This would contain actual dashboard queries
    # For now, returning mock data
    
    stats = ReportDashboardStats(
        total_templates=0,
        active_schedules=0,
        pending_reports=0,
        completed_reports_today=0,
        failed_reports_today=0,
        total_downloads_today=0,
        storage_used_mb=0.0,
        most_popular_template=None,
        recent_reports=[]
    )
    
    return stats

# Maintenance endpoints
@router.post("/cleanup", summary="Clean up expired reports")
async def cleanup_expired_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clean up expired reports (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform cleanup operations"
        )
    
    report_service = ReportService(db)
    cleaned_count = report_service.cleanup_expired_reports()
    
    return {"message": f"Cleaned up {cleaned_count} expired reports"}

# Health check endpoint
@router.get("/health", summary="Report service health check")
async def health_check():
    """Check the health of the report service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "report_generation"
    }
