from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database.database import get_db
from app.models.bi_analytics import (
    ClinicalMetric, MetricValue, MetricAlert, Dashboard, DashboardWidget,
    BIReport, BIReportGeneration, PerformanceBenchmark, AnalyticsInsight,
    DataQualityCheck, DataQualityResult
)
from app.models.user import User
from app.schemas.bi_analytics import (
    ClinicalMetricCreate, ClinicalMetricUpdate, ClinicalMetric as ClinicalMetricSchema,
    MetricValueCreate, MetricValueUpdate, MetricValue as MetricValueSchema,
    MetricAlertCreate, MetricAlertUpdate, MetricAlert as MetricAlertSchema,
    DashboardCreate, DashboardUpdate, Dashboard as DashboardSchema,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidget as DashboardWidgetSchema,
    BIReportCreate, BIReportUpdate, BIReport as BIReportSchema,
    BIReportGenerationCreate, BIReportGenerationUpdate, BIReportGeneration as BIReportGenerationSchema,
    PerformanceBenchmarkCreate, PerformanceBenchmarkUpdate, PerformanceBenchmark as PerformanceBenchmarkSchema,
    AnalyticsInsightCreate, AnalyticsInsightUpdate, AnalyticsInsight as AnalyticsInsightSchema,
    DataQualityCheckCreate, DataQualityCheckUpdate, DataQualityCheck as DataQualityCheckSchema,
    DataQualityResultCreate, DataQualityResult as DataQualityResultSchema,
    MetricCalculationRequest, DashboardDataRequest, BIReportGenerationRequest,
    AnalyticsInsightRequest, MetricTrend, PerformanceComparison,
    BIInsightsSummary, DataQualitySummary
)
from app.services.auth_service import AuthService
from app.services.bi_analytics_service import BIAnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get current user
def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
    return current_user

# Clinical Metrics endpoints
@router.get("/metrics", response_model=List[ClinicalMetricSchema], summary="Get all clinical metrics")
async def get_clinical_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metric_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get all clinical metrics with filtering options"""
    query = db.query(ClinicalMetric)
    
    if metric_type:
        query = query.filter(ClinicalMetric.metric_type == metric_type)
    
    if status:
        query = query.filter(ClinicalMetric.status == status)
    
    metrics = query.offset(skip).limit(limit).all()
    return metrics

@router.get("/metrics/{metric_id}", response_model=ClinicalMetricSchema, summary="Get clinical metric by ID")
async def get_clinical_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific clinical metric by ID"""
    metric = db.query(ClinicalMetric).filter(ClinicalMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical metric not found")
    return metric

@router.post("/metrics", response_model=ClinicalMetricSchema, status_code=status.HTTP_201_CREATED, summary="Create new clinical metric")
async def create_clinical_metric(
    metric_data: ClinicalMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new clinical metric"""
    metric = ClinicalMetric(
        **metric_data.dict(),
        created_by=current_user.id
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

@router.put("/metrics/{metric_id}", response_model=ClinicalMetricSchema, summary="Update clinical metric")
async def update_clinical_metric(
    metric_id: int,
    metric_data: ClinicalMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a clinical metric"""
    metric = db.query(ClinicalMetric).filter(ClinicalMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical metric not found")
    
    # Check if user can modify this metric
    if metric.is_system_metric and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify system metrics"
        )
    
    update_data = metric_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(metric, field, value)
    
    db.commit()
    db.refresh(metric)
    return metric

@router.delete("/metrics/{metric_id}", summary="Delete clinical metric")
async def delete_clinical_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a clinical metric"""
    metric = db.query(ClinicalMetric).filter(ClinicalMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical metric not found")
    
    # Check if user can delete this metric
    if metric.is_system_metric and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete system metrics"
        )
    
    # Soft delete by setting status to inactive
    metric.status = "inactive"
    db.commit()
    return {"message": "Clinical metric deactivated successfully"}

# Metric Calculation endpoints
@router.post("/metrics/calculate", summary="Calculate metric value")
async def calculate_metric(
    request: MetricCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate metric value for a specific period"""
    try:
        bi_service = BIAnalyticsService(db)
        result = bi_service.calculate_metric(request)
        return result
    except Exception as e:
        logger.error(f"Error calculating metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate metric: {str(e)}"
        )

# Metric Values endpoints
@router.get("/metric-values", response_model=List[MetricValueSchema], summary="Get metric values")
async def get_metric_values(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metric_id: Optional[int] = Query(None),
    period_type: Optional[str] = Query(None)
):
    """Get metric values with filtering options"""
    query = db.query(MetricValue)
    
    if metric_id:
        query = query.filter(MetricValue.metric_id == metric_id)
    
    if period_type:
        query = query.filter(MetricValue.period_type == period_type)
    
    values = query.order_by(MetricValue.calculated_at.desc()).offset(skip).limit(limit).all()
    return values

@router.get("/metric-values/{value_id}", response_model=MetricValueSchema, summary="Get metric value by ID")
async def get_metric_value(
    value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific metric value by ID"""
    value = db.query(MetricValue).filter(MetricValue.id == value_id).first()
    if not value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric value not found")
    return value

# Metric Alerts endpoints
@router.get("/alerts", response_model=List[MetricAlertSchema], summary="Get metric alerts")
async def get_metric_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None)
):
    """Get metric alerts with filtering options"""
    query = db.query(MetricAlert)
    
    if status:
        query = query.filter(MetricAlert.status == status)
    
    if alert_type:
        query = query.filter(MetricAlert.alert_type == alert_type)
    
    alerts = query.order_by(MetricAlert.triggered_at.desc()).offset(skip).limit(limit).all()
    return alerts

@router.get("/alerts/{alert_id}", response_model=MetricAlertSchema, summary="Get metric alert by ID")
async def get_metric_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific metric alert by ID"""
    alert = db.query(MetricAlert).filter(MetricAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric alert not found")
    return alert

@router.put("/alerts/{alert_id}/acknowledge", response_model=MetricAlertSchema, summary="Acknowledge metric alert")
async def acknowledge_metric_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge a metric alert"""
    alert = db.query(MetricAlert).filter(MetricAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    return alert

@router.put("/alerts/{alert_id}/resolve", response_model=MetricAlertSchema, summary="Resolve metric alert")
async def resolve_metric_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve a metric alert"""
    alert = db.query(MetricAlert).filter(MetricAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric alert not found")
    
    alert.status = "resolved"
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    return alert

# Dashboard endpoints
@router.get("/dashboards", response_model=List[DashboardSchema], summary="Get all dashboards")
async def get_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_public: Optional[bool] = Query(None)
):
    """Get all dashboards with filtering options"""
    query = db.query(Dashboard)
    
    if is_public is not None:
        query = query.filter(Dashboard.is_public == is_public)
    
    dashboards = query.offset(skip).limit(limit).all()
    return dashboards

@router.get("/dashboards/{dashboard_id}", response_model=DashboardSchema, summary="Get dashboard by ID")
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific dashboard by ID"""
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dashboard

@router.post("/dashboards", response_model=DashboardSchema, status_code=status.HTTP_201_CREATED, summary="Create new dashboard")
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard"""
    dashboard = Dashboard(
        **dashboard_data.dict(),
        created_by=current_user.id
    )
    
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.put("/dashboards/{dashboard_id}", response_model=DashboardSchema, summary="Update dashboard")
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard"""
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    # Check if user can modify this dashboard
    if dashboard.is_system_dashboard and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify system dashboards"
        )
    
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
    """Get data for dashboard widgets"""
    try:
        request.dashboard_id = dashboard_id
        bi_service = BIAnalyticsService(db)
        result = bi_service.get_dashboard_data(request)
        return result
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

# Dashboard Widgets endpoints
@router.get("/dashboards/{dashboard_id}/widgets", response_model=List[DashboardWidgetSchema], summary="Get dashboard widgets")
async def get_dashboard_widgets(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get widgets for a specific dashboard"""
    widgets = db.query(DashboardWidget).filter(
        DashboardWidget.dashboard_id == dashboard_id,
        DashboardWidget.is_active == True
    ).all()
    return widgets

@router.post("/dashboards/{dashboard_id}/widgets", response_model=DashboardWidgetSchema, status_code=status.HTTP_201_CREATED, summary="Create dashboard widget")
async def create_dashboard_widget(
    dashboard_id: int,
    widget_data: DashboardWidgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard widget"""
    widget = DashboardWidget(
        **widget_data.dict(),
        dashboard_id=dashboard_id
    )
    
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget

@router.put("/widgets/{widget_id}", response_model=DashboardWidgetSchema, summary="Update dashboard widget")
async def update_dashboard_widget(
    widget_id: int,
    widget_data: DashboardWidgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard widget"""
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard widget not found")
    
    update_data = widget_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)
    
    db.commit()
    db.refresh(widget)
    return widget

@router.delete("/widgets/{widget_id}", summary="Delete dashboard widget")
async def delete_dashboard_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard widget"""
    widget = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard widget not found")
    
    # Soft delete by setting is_active to False
    widget.is_active = False
    db.commit()
    return {"message": "Dashboard widget deactivated successfully"}

# BI Reports endpoints
@router.get("/reports", response_model=List[BIReportSchema], summary="Get all BI reports")
async def get_bi_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[str] = Query(None)
):
    """Get all BI reports with filtering options"""
    query = db.query(BIReport)
    
    if report_type:
        query = query.filter(BIReport.report_type == report_type)
    
    reports = query.offset(skip).limit(limit).all()
    return reports

@router.get("/reports/{report_id}", response_model=BIReportSchema, summary="Get BI report by ID")
async def get_bi_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific BI report by ID"""
    report = db.query(BIReport).filter(BIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BI report not found")
    return report

@router.post("/reports", response_model=BIReportSchema, status_code=status.HTTP_201_CREATED, summary="Create new BI report")
async def create_bi_report(
    report_data: BIReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new BI report"""
    report = BIReport(
        **report_data.dict(),
        created_by=current_user.id
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.post("/reports/{report_id}/generate", summary="Generate BI report")
async def generate_bi_report(
    report_id: int,
    request: BIReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a BI report"""
    try:
        request.report_id = report_id
        bi_service = BIAnalyticsService(db)
        result = bi_service.generate_bi_report(request)
        return result
    except Exception as e:
        logger.error(f"Error generating BI report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate BI report: {str(e)}"
        )

# Analytics Insights endpoints
@router.get("/insights", response_model=List[AnalyticsInsightSchema], summary="Get analytics insights")
async def get_analytics_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    insight_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get analytics insights with filtering options"""
    query = db.query(AnalyticsInsight)
    
    if insight_type:
        query = query.filter(AnalyticsInsight.insight_type == insight_type)
    
    if category:
        query = query.filter(AnalyticsInsight.category == category)
    
    if status:
        query = query.filter(AnalyticsInsight.status == status)
    
    insights = query.order_by(AnalyticsInsight.generated_at.desc()).offset(skip).limit(limit).all()
    return insights

@router.get("/insights/{insight_id}", response_model=AnalyticsInsightSchema, summary="Get analytics insight by ID")
async def get_analytics_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific analytics insight by ID"""
    insight = db.query(AnalyticsInsight).filter(AnalyticsInsight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics insight not found")
    return insight

@router.post("/insights/generate", response_model=List[AnalyticsInsightSchema], summary="Generate analytics insights")
async def generate_analytics_insights(
    request: AnalyticsInsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered analytics insights"""
    try:
        bi_service = BIAnalyticsService(db)
        insights = bi_service.generate_analytics_insights(request)
        return insights
    except Exception as e:
        logger.error(f"Error generating analytics insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics insights: {str(e)}"
        )

@router.put("/insights/{insight_id}/review", response_model=AnalyticsInsightSchema, summary="Review analytics insight")
async def review_analytics_insight(
    insight_id: int,
    status: str,
    action_taken: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and update analytics insight status"""
    insight = db.query(AnalyticsInsight).filter(AnalyticsInsight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics insight not found")
    
    insight.status = status
    insight.reviewed_by = current_user.id
    insight.reviewed_at = datetime.utcnow()
    insight.action_taken = action_taken
    
    db.commit()
    db.refresh(insight)
    return insight

# Performance Comparison endpoints
@router.get("/performance/{metric_id}/comparison", response_model=PerformanceComparison, summary="Get performance comparison")
async def get_performance_comparison(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance comparison for a metric"""
    try:
        bi_service = BIAnalyticsService(db)
        comparison = bi_service.get_performance_comparison(metric_id)
        return comparison
    except Exception as e:
        logger.error(f"Error getting performance comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance comparison: {str(e)}"
        )

# Summary endpoints
@router.get("/insights/summary", response_model=BIInsightsSummary, summary="Get BI insights summary")
async def get_bi_insights_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of BI insights"""
    try:
        bi_service = BIAnalyticsService(db)
        summary = bi_service.get_bi_insights_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting BI insights summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get BI insights summary: {str(e)}"
        )

@router.get("/data-quality/summary", response_model=DataQualitySummary, summary="Get data quality summary")
async def get_data_quality_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data quality summary"""
    try:
        bi_service = BIAnalyticsService(db)
        summary = bi_service.get_data_quality_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting data quality summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data quality summary: {str(e)}"
        )

# Health check endpoint
@router.get("/health", summary="BI Analytics service health check")
async def health_check():
    """Check the health of the BI Analytics service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "bi_analytics",
        "features": {
            "metrics_calculation": True,
            "dashboard_generation": True,
            "insights_generation": True,
            "report_generation": True,
            "data_quality_monitoring": True
        }
    }
