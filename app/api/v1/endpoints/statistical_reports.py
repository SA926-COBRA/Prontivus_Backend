from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging

from app.database.database import get_db
from app.models.statistical_reports import (
    StatisticalReport, ReportTemplate, ReportGeneration, ReportMetric,
    ReportMetricValue, ReportDashboard, ReportAccessLog, ReportSchedule
)
from app.models.user import User
from app.schemas.statistical_reports import (
    StatisticalReportCreate, StatisticalReportUpdate, StatisticalReport as StatisticalReportSchema,
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplate as ReportTemplateSchema,
    ReportGeneration as ReportGenerationSchema,
    ReportMetricCreate, ReportMetricUpdate, ReportMetric as ReportMetricSchema,
    ReportMetricValue as ReportMetricValueSchema,
    ReportDashboardCreate, ReportDashboardUpdate, ReportDashboard as ReportDashboardSchema,
    ReportAccessLog as ReportAccessLogSchema,
    ReportScheduleCreate, ReportScheduleUpdate, ReportSchedule as ReportScheduleSchema,
    ReportSearchRequest, ReportGenerationRequest, ReportSummary,
    MetricCalculationRequest, DashboardDataRequest, ReportAnalytics
)
from app.services.auth_service import AuthService
from app.services.statistical_reports_service import StatisticalReportsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Statistical Report endpoints
@router.get("/reports", response_model=List[StatisticalReportSchema], summary="Get statistical reports")
async def get_statistical_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_name: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get statistical reports with filtering options"""
    try:
        service = StatisticalReportsService(db)
        request = ReportSearchRequest(
            report_name=report_name,
            report_type=report_type,
            status=status,
            created_by=created_by,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        reports = service.search_reports(request)
        return reports
    except Exception as e:
        logger.error(f"Error getting statistical reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reports: {str(e)}"
        )

@router.get("/reports/{report_id}", response_model=StatisticalReportSchema, summary="Get statistical report by ID")
async def get_statistical_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific statistical report by ID"""
    report = db.query(StatisticalReport).filter(StatisticalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistical report not found")
    return report

@router.post("/reports", response_model=StatisticalReportSchema, status_code=status.HTTP_201_CREATED, summary="Create statistical report")
async def create_statistical_report(
    report_data: StatisticalReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new statistical report"""
    try:
        service = StatisticalReportsService(db)
        report = service.create_report(report_data.dict(), current_user.id)
        return report
    except Exception as e:
        logger.error(f"Error creating statistical report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}"
        )

@router.put("/reports/{report_id}", response_model=StatisticalReportSchema, summary="Update statistical report")
async def update_statistical_report(
    report_id: int,
    report_data: StatisticalReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a statistical report"""
    report = db.query(StatisticalReport).filter(StatisticalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistical report not found")
    
    update_data = report_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    db.commit()
    db.refresh(report)
    return report

@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete statistical report")
async def delete_statistical_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a statistical report"""
    report = db.query(StatisticalReport).filter(StatisticalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statistical report not found")
    
    db.delete(report)
    db.commit()

# Report Generation endpoints
@router.post("/reports/{report_id}/generate", response_model=ReportGenerationSchema, summary="Generate statistical report")
async def generate_statistical_report(
    report_id: int,
    request: ReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a statistical report"""
    try:
        request.report_id = report_id
        service = StatisticalReportsService(db)
        generation = service.generate_report(request, current_user.id)
        return generation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating statistical report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.get("/reports/{report_id}/generations", response_model=List[ReportGenerationSchema], summary="Get report generations")
async def get_report_generations(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get generations for a specific report"""
    generations = db.query(ReportGeneration).filter(
        ReportGeneration.report_id == report_id
    ).order_by(desc(ReportGeneration.generation_start)).all()
    return generations

# Report Template endpoints
@router.get("/templates", response_model=List[ReportTemplateSchema], summary="Get report templates")
async def get_report_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    template_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get report templates with filtering options"""
    query = db.query(ReportTemplate)
    
    if template_type:
        query = query.filter(ReportTemplate.template_type == template_type)
    
    if is_active is not None:
        query = query.filter(ReportTemplate.is_active == is_active)
    
    templates = query.offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=ReportTemplateSchema, summary="Get report template by ID")
async def get_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report template by ID"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    return template

@router.post("/templates", response_model=ReportTemplateSchema, status_code=status.HTTP_201_CREATED, summary="Create report template")
async def create_report_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report template"""
    template = ReportTemplate(**template_data.dict(), created_by=current_user.id)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.put("/templates/{template_id}", response_model=ReportTemplateSchema, summary="Update report template")
async def update_report_template(
    template_id: int,
    template_data: ReportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report template"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report template not found")
    
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template

# Report Metric endpoints
@router.get("/metrics", response_model=List[ReportMetricSchema], summary="Get report metrics")
async def get_report_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metric_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get report metrics with filtering options"""
    query = db.query(ReportMetric)
    
    if metric_type:
        query = query.filter(ReportMetric.metric_type == metric_type)
    
    if is_active is not None:
        query = query.filter(ReportMetric.is_active == is_active)
    
    metrics = query.offset(skip).limit(limit).all()
    return metrics

@router.get("/metrics/{metric_id}", response_model=ReportMetricSchema, summary="Get report metric by ID")
async def get_report_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report metric by ID"""
    metric = db.query(ReportMetric).filter(ReportMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report metric not found")
    return metric

@router.post("/metrics", response_model=ReportMetricSchema, status_code=status.HTTP_201_CREATED, summary="Create report metric")
async def create_report_metric(
    metric_data: ReportMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report metric"""
    metric = ReportMetric(**metric_data.dict(), created_by=current_user.id)
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

@router.put("/metrics/{metric_id}", response_model=ReportMetricSchema, summary="Update report metric")
async def update_report_metric(
    metric_id: int,
    metric_data: ReportMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report metric"""
    metric = db.query(ReportMetric).filter(ReportMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report metric not found")
    
    update_data = metric_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(metric, field, value)
    
    db.commit()
    db.refresh(metric)
    return metric

# Metric Calculation endpoints
@router.post("/metrics/{metric_id}/calculate", response_model=ReportMetricValueSchema, summary="Calculate metric value")
async def calculate_metric_value(
    metric_id: int,
    request: MetricCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate metric value for a specific period"""
    try:
        request.metric_id = metric_id
        service = StatisticalReportsService(db)
        metric_value = service.calculate_metric(request)
        return metric_value
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating metric value: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metric: {str(e)}"
        )

@router.get("/metrics/{metric_id}/values", response_model=List[ReportMetricValueSchema], summary="Get metric values")
async def get_metric_values(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get values for a specific metric"""
    values = db.query(ReportMetricValue).filter(
        ReportMetricValue.metric_id == metric_id
    ).order_by(desc(ReportMetricValue.calculated_at)).offset(skip).limit(limit).all()
    return values

# Report Dashboard endpoints
@router.get("/dashboards", response_model=List[ReportDashboardSchema], summary="Get report dashboards")
async def get_report_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None)
):
    """Get report dashboards with filtering options"""
    query = db.query(ReportDashboard)
    
    if is_active is not None:
        query = query.filter(ReportDashboard.is_active == is_active)
    
    if is_public is not None:
        query = query.filter(ReportDashboard.is_public == is_public)
    
    dashboards = query.offset(skip).limit(limit).all()
    return dashboards

@router.get("/dashboards/{dashboard_id}", response_model=ReportDashboardSchema, summary="Get report dashboard by ID")
async def get_report_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific report dashboard by ID"""
    dashboard = db.query(ReportDashboard).filter(ReportDashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report dashboard not found")
    return dashboard

@router.post("/dashboards", response_model=ReportDashboardSchema, status_code=status.HTTP_201_CREATED, summary="Create report dashboard")
async def create_report_dashboard(
    dashboard_data: ReportDashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report dashboard"""
    dashboard = ReportDashboard(**dashboard_data.dict(), created_by=current_user.id)
    
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.put("/dashboards/{dashboard_id}", response_model=ReportDashboardSchema, summary="Update report dashboard")
async def update_report_dashboard(
    dashboard_id: int,
    dashboard_data: ReportDashboardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a report dashboard"""
    dashboard = db.query(ReportDashboard).filter(ReportDashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report dashboard not found")
    
    update_data = dashboard_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dashboard, field, value)
    
    db.commit()
    db.refresh(dashboard)
    return dashboard

# Dashboard Data endpoints
@router.post("/dashboards/{dashboard_id}/data", summary="Get dashboard data")
async def get_dashboard_data(
    dashboard_id: int,
    request: DashboardDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard data"""
    try:
        request.dashboard_id = dashboard_id
        service = StatisticalReportsService(db)
        dashboard_data = service.get_dashboard_data(request)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

# Summary endpoints
@router.get("/summary", response_model=ReportSummary, summary="Get report summary")
async def get_report_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report summary statistics"""
    try:
        service = StatisticalReportsService(db)
        summary = service.get_report_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting report summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report summary: {str(e)}"
        )

@router.get("/analytics", response_model=ReportAnalytics, summary="Get report analytics")
async def get_report_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed report analytics"""
    try:
        service = StatisticalReportsService(db)
        analytics = service.get_report_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting report analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report analytics: {str(e)}"
        )

# Health check endpoint
@router.get("/health", summary="Statistical reports service health check")
async def health_check():
    """Check the health of the Statistical Reports service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "statistical_reports",
        "features": {
            "report_generation": True,
            "templates": True,
            "metrics": True,
            "dashboards": True,
            "analytics": True
        }
    }
