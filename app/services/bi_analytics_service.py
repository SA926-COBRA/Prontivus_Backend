import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from app.models.bi_analytics import (
    ClinicalMetric, MetricValue, MetricAlert, Dashboard, DashboardWidget,
    BIReport, BIReportGeneration, PerformanceBenchmark, AnalyticsInsight,
    DataQualityCheck, DataQualityResult
)
from app.schemas.bi_analytics import (
    MetricCalculationRequest, DashboardDataRequest, BIReportGenerationRequest,
    AnalyticsInsightRequest, MetricTrend, PerformanceComparison,
    BIInsightsSummary, DataQualitySummary
)

logger = logging.getLogger(__name__)

class BIAnalyticsService:
    """Service for Business Intelligence and Analytics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = {}  # Simple in-memory cache for demo purposes
    
    def calculate_metric(self, request: MetricCalculationRequest) -> Dict[str, Any]:
        """Calculate metric value for a specific period"""
        try:
            metric = self.db.query(ClinicalMetric).filter(
                ClinicalMetric.id == request.metric_id
            ).first()
            
            if not metric:
                raise ValueError("Metric not found")
            
            # Execute calculation based on metric configuration
            if metric.calculation_method.startswith("SELECT"):
                # Direct SQL query
                query = metric.calculation_method
                params = {
                    'start_date': request.period_start,
                    'end_date': request.period_end
                }
                
                # Add filters if provided
                if request.filters:
                    params.update(request.filters)
                
                result = self.db.execute(text(query), params)
                value = result.scalar()
                
            else:
                # Formula-based calculation
                value = self._calculate_formula_metric(
                    metric, request.period_start, request.period_end, request.filters
                )
            
            # Create metric value record
            metric_value = MetricValue(
                metric_id=request.metric_id,
                value=float(value) if value is not None else 0.0,
                period_start=request.period_start,
                period_end=request.period_end,
                period_type="daily",  # Default, can be configured
                data_points_count=1,
                confidence_score=0.95
            )
            
            self.db.add(metric_value)
            self.db.commit()
            
            # Check for threshold breaches
            self._check_metric_thresholds(metric, metric_value.value)
            
            return {
                "metric_id": request.metric_id,
                "value": metric_value.value,
                "period_start": request.period_start,
                "period_end": request.period_end,
                "calculated_at": metric_value.calculated_at
            }
            
        except Exception as e:
            logger.error(f"Error calculating metric: {e}")
            raise
    
    def _calculate_formula_metric(
        self, 
        metric: ClinicalMetric, 
        period_start: datetime, 
        period_end: datetime, 
        filters: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate metric using formula-based approach"""
        try:
            # This is a simplified implementation
            # In production, you'd have a more sophisticated formula engine
            
            if metric.calculation_method == "patient_satisfaction_score":
                # Mock calculation for patient satisfaction
                return np.random.uniform(3.5, 4.8)
            
            elif metric.calculation_method == "average_wait_time":
                # Mock calculation for average wait time
                return np.random.uniform(15, 45)
            
            elif metric.calculation_method == "readmission_rate":
                # Mock calculation for readmission rate
                return np.random.uniform(0.05, 0.15)
            
            elif metric.calculation_method == "revenue_per_patient":
                # Mock calculation for revenue per patient
                return np.random.uniform(500, 2000)
            
            else:
                # Default random value for unknown metrics
                return np.random.uniform(0, 100)
                
        except Exception as e:
            logger.error(f"Error in formula calculation: {e}")
            return 0.0
    
    def _check_metric_thresholds(self, metric: ClinicalMetric, value: float):
        """Check if metric value breaches thresholds and create alerts"""
        try:
            if metric.threshold_warning and value >= metric.threshold_warning:
                alert = MetricAlert(
                    metric_id=metric.id,
                    alert_type="warning",
                    threshold_breached=metric.threshold_warning,
                    current_value=value,
                    message=f"Metric {metric.metric_name} has exceeded warning threshold"
                )
                self.db.add(alert)
            
            if metric.threshold_critical and value >= metric.threshold_critical:
                alert = MetricAlert(
                    metric_id=metric.id,
                    alert_type="critical",
                    threshold_breached=metric.threshold_critical,
                    current_value=value,
                    message=f"Metric {metric.metric_name} has exceeded critical threshold"
                )
                self.db.add(alert)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error checking metric thresholds: {e}")
    
    def get_dashboard_data(self, request: DashboardDataRequest) -> Dict[str, Any]:
        """Get data for dashboard widgets"""
        try:
            dashboard = self.db.query(Dashboard).filter(
                Dashboard.id == request.dashboard_id
            ).first()
            
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            widgets = self.db.query(DashboardWidget).filter(
                DashboardWidget.dashboard_id == request.dashboard_id,
                DashboardWidget.is_active == True
            ).all()
            
            widget_data = []
            for widget in widgets:
                data = self._get_widget_data(widget, request.filters)
                widget_data.append({
                    "widget_id": widget.id,
                    "widget_type": widget.widget_type,
                    "title": widget.title,
                    "config": widget.config,
                    "data": data
                })
            
            return {
                "dashboard_id": request.dashboard_id,
                "dashboard_name": dashboard.name,
                "widgets": widget_data,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
    
    def _get_widget_data(self, widget: DashboardWidget, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            if widget.widget_type == "metric":
                return self._get_metric_widget_data(widget, filters)
            elif widget.widget_type == "chart":
                return self._get_chart_widget_data(widget, filters)
            elif widget.widget_type == "table":
                return self._get_table_widget_data(widget, filters)
            elif widget.widget_type == "kpi":
                return self._get_kpi_widget_data(widget, filters)
            else:
                return {"error": "Unknown widget type"}
                
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {"error": str(e)}
    
    def _get_metric_widget_data(self, widget: DashboardWidget, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data for metric widget"""
        if not widget.metric_id:
            return {"error": "No metric configured"}
        
        # Get latest metric value
        latest_value = self.db.query(MetricValue).filter(
            MetricValue.metric_id == widget.metric_id
        ).order_by(MetricValue.calculated_at.desc()).first()
        
        if not latest_value:
            return {"value": 0, "trend": "stable", "change": 0}
        
        # Get previous value for trend calculation
        previous_value = self.db.query(MetricValue).filter(
            MetricValue.metric_id == widget.metric_id,
            MetricValue.calculated_at < latest_value.calculated_at
        ).order_by(MetricValue.calculated_at.desc()).first()
        
        trend = "stable"
        change = 0
        
        if previous_value:
            change = ((latest_value.value - previous_value.value) / previous_value.value) * 100
            if change > 5:
                trend = "up"
            elif change < -5:
                trend = "down"
        
        return {
            "value": latest_value.value,
            "trend": trend,
            "change": round(change, 2),
            "last_updated": latest_value.calculated_at
        }
    
    def _get_chart_widget_data(self, widget: DashboardWidget, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data for chart widget"""
        if not widget.metric_id:
            return {"error": "No metric configured"}
        
        # Get historical data for the metric
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        values = self.db.query(MetricValue).filter(
            MetricValue.metric_id == widget.metric_id,
            MetricValue.period_start >= start_date,
            MetricValue.period_start <= end_date
        ).order_by(MetricValue.period_start).all()
        
        chart_data = {
            "labels": [v.period_start.strftime("%Y-%m-%d") for v in values],
            "datasets": [{
                "label": widget.title,
                "data": [v.value for v in values],
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.1)"
            }]
        }
        
        return chart_data
    
    def _get_table_widget_data(self, widget: DashboardWidget, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data for table widget"""
        # Mock table data
        return {
            "columns": ["Metric", "Value", "Trend", "Status"],
            "rows": [
                ["Patient Satisfaction", "4.2", "↑", "Good"],
                ["Average Wait Time", "25 min", "↓", "Excellent"],
                ["Readmission Rate", "8.5%", "→", "Needs Improvement"],
                ["Revenue per Patient", "$1,250", "↑", "Good"]
            ]
        }
    
    def _get_kpi_widget_data(self, widget: DashboardWidget, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data for KPI widget"""
        # Mock KPI data
        return {
            "current_value": 85,
            "target_value": 90,
            "status": "good",
            "progress": 85,
            "trend": "up",
            "change": 5.2
        }
    
    def generate_bi_report(self, request: BIReportGenerationRequest) -> Dict[str, Any]:
        """Generate BI report"""
        try:
            report = self.db.query(BIReport).filter(
                BIReport.id == request.report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Create report generation record
            generation = BIReportGeneration(
                report_id=request.report_id,
                generation_date=datetime.utcnow(),
                data_period_start=request.data_period_start,
                data_period_end=request.data_period_end,
                status="generating"
            )
            
            self.db.add(generation)
            self.db.commit()
            
            # Generate report content
            report_data = self._generate_report_content(report, request)
            
            # Update generation record
            generation.status = "completed"
            generation.processing_time_seconds = 30.0  # Mock processing time
            generation.file_path = f"/reports/{generation.id}.pdf"  # Mock file path
            generation.file_size = 1024000  # Mock file size
            
            self.db.commit()
            
            return {
                "generation_id": generation.id,
                "status": "completed",
                "file_path": generation.file_path,
                "processing_time": generation.processing_time_seconds
            }
            
        except Exception as e:
            logger.error(f"Error generating BI report: {e}")
            raise
    
    def _generate_report_content(self, report: BIReport, request: BIReportGenerationRequest) -> Dict[str, Any]:
        """Generate report content based on template configuration"""
        try:
            # Mock report content generation
            content = {
                "title": report.report_name,
                "generated_at": datetime.utcnow(),
                "period": {
                    "start": request.data_period_start,
                    "end": request.data_period_end
                },
                "sections": [
                    {
                        "title": "Executive Summary",
                        "content": "This report provides an overview of key performance indicators and insights."
                    },
                    {
                        "title": "Key Metrics",
                        "content": "Patient satisfaction: 4.2/5, Average wait time: 25 minutes, Readmission rate: 8.5%"
                    },
                    {
                        "title": "Recommendations",
                        "content": "Focus on reducing wait times and improving patient communication."
                    }
                ]
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating report content: {e}")
            return {}
    
    def generate_analytics_insights(self, request: AnalyticsInsightRequest) -> List[AnalyticsInsight]:
        """Generate AI-powered analytics insights"""
        try:
            insights = []
            
            # Mock insight generation using simple algorithms
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=request.data_period_days)
            
            # Generate trend insights
            if not request.insight_type or request.insight_type == "trend":
                trend_insights = self._generate_trend_insights(start_date, end_date)
                insights.extend(trend_insights)
            
            # Generate anomaly insights
            if not request.insight_type or request.insight_type == "anomaly":
                anomaly_insights = self._generate_anomaly_insights(start_date, end_date)
                insights.extend(anomaly_insights)
            
            # Generate recommendations
            if not request.insight_type or request.insight_type == "recommendation":
                recommendation_insights = self._generate_recommendation_insights(start_date, end_date)
                insights.extend(recommendation_insights)
            
            # Save insights to database
            for insight in insights:
                self.db.add(insight)
            
            self.db.commit()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating analytics insights: {e}")
            raise
    
    def _generate_trend_insights(self, start_date: datetime, end_date: datetime) -> List[AnalyticsInsight]:
        """Generate trend-based insights"""
        insights = []
        
        # Mock trend analysis
        trends = [
            {
                "title": "Patient Satisfaction Trending Upward",
                "description": "Patient satisfaction scores have increased by 12% over the last 30 days, indicating improved service quality.",
                "confidence": 0.85,
                "impact": "high",
                "category": "clinical"
            },
            {
                "title": "Wait Times Decreasing",
                "description": "Average patient wait times have decreased by 8 minutes over the past month, showing operational efficiency improvements.",
                "confidence": 0.78,
                "impact": "medium",
                "category": "operational"
            }
        ]
        
        for trend in trends:
            insight = AnalyticsInsight(
                insight_type="trend",
                title=trend["title"],
                description=trend["description"],
                confidence_score=trend["confidence"],
                impact_level=trend["impact"],
                category=trend["category"],
                data_period_start=start_date,
                data_period_end=end_date,
                ai_model_version="1.0",
                processing_parameters={"algorithm": "linear_regression"}
            )
            insights.append(insight)
        
        return insights
    
    def _generate_anomaly_insights(self, start_date: datetime, end_date: datetime) -> List[AnalyticsInsight]:
        """Generate anomaly detection insights"""
        insights = []
        
        # Mock anomaly detection
        anomalies = [
            {
                "title": "Unusual Spike in Readmission Rate",
                "description": "Readmission rate increased by 25% on March 15th, which is 3 standard deviations above the mean. This may indicate a quality issue.",
                "confidence": 0.92,
                "impact": "critical",
                "category": "quality"
            }
        ]
        
        for anomaly in anomalies:
            insight = AnalyticsInsight(
                insight_type="anomaly",
                title=anomaly["title"],
                description=anomaly["description"],
                confidence_score=anomaly["confidence"],
                impact_level=anomaly["impact"],
                category=anomaly["category"],
                data_period_start=start_date,
                data_period_end=end_date,
                ai_model_version="1.0",
                processing_parameters={"algorithm": "isolation_forest"}
            )
            insights.append(insight)
        
        return insights
    
    def _generate_recommendation_insights(self, start_date: datetime, end_date: datetime) -> List[AnalyticsInsight]:
        """Generate recommendation insights"""
        insights = []
        
        # Mock recommendations
        recommendations = [
            {
                "title": "Optimize Staff Scheduling",
                "description": "Based on patient volume patterns, consider adjusting staff schedules to reduce peak-hour wait times by 15%.",
                "confidence": 0.80,
                "impact": "medium",
                "category": "operational"
            },
            {
                "title": "Implement Patient Communication System",
                "description": "Patient satisfaction scores indicate a need for better communication. Implementing a patient portal could improve scores by 20%.",
                "confidence": 0.75,
                "impact": "high",
                "category": "clinical"
            }
        ]
        
        for rec in recommendations:
            insight = AnalyticsInsight(
                insight_type="recommendation",
                title=rec["title"],
                description=rec["description"],
                confidence_score=rec["confidence"],
                impact_level=rec["impact"],
                category=rec["category"],
                data_period_start=start_date,
                data_period_end=end_date,
                ai_model_version="1.0",
                processing_parameters={"algorithm": "rule_based"}
            )
            insights.append(insight)
        
        return insights
    
    def get_performance_comparison(self, metric_id: int) -> PerformanceComparison:
        """Get performance comparison for a metric"""
        try:
            metric = self.db.query(ClinicalMetric).filter(
                ClinicalMetric.id == metric_id
            ).first()
            
            if not metric:
                raise ValueError("Metric not found")
            
            # Get current value
            current_value = self.db.query(MetricValue).filter(
                MetricValue.metric_id == metric_id
            ).order_by(MetricValue.calculated_at.desc()).first()
            
            if not current_value:
                current_value = 0.0
            else:
                current_value = current_value.value
            
            # Get benchmark data
            benchmark = self.db.query(PerformanceBenchmark).filter(
                PerformanceBenchmark.metric_type == metric.metric_type,
                PerformanceBenchmark.is_active == True
            ).first()
            
            target_value = metric.target_value or (benchmark.target_value if benchmark else 0)
            industry_average = benchmark.industry_average if benchmark else None
            
            # Calculate performance score
            if target_value > 0:
                performance_score = min(100, (current_value / target_value) * 100)
            else:
                performance_score = 0
            
            # Determine status
            if performance_score >= 90:
                status = "excellent"
            elif performance_score >= 75:
                status = "good"
            elif performance_score >= 60:
                status = "needs_improvement"
            else:
                status = "poor"
            
            return PerformanceComparison(
                metric_id=metric_id,
                metric_name=metric.metric_name,
                current_value=current_value,
                target_value=target_value,
                industry_average=industry_average,
                peer_average=None,  # Would be calculated from peer data
                performance_score=performance_score,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting performance comparison: {e}")
            raise
    
    def get_bi_insights_summary(self) -> BIInsightsSummary:
        """Get summary of BI insights"""
        try:
            # Get total insights
            total_insights = self.db.query(AnalyticsInsight).count()
            
            # Get insights by type
            insights_by_type = {}
            for insight_type in ["trend", "anomaly", "recommendation", "prediction"]:
                count = self.db.query(AnalyticsInsight).filter(
                    AnalyticsInsight.insight_type == insight_type
                ).count()
                insights_by_type[insight_type] = count
            
            # Get insights by category
            insights_by_category = {}
            for category in ["clinical", "financial", "operational", "quality"]:
                count = self.db.query(AnalyticsInsight).filter(
                    AnalyticsInsight.category == category
                ).count()
                insights_by_category[category] = count
            
            # Get high impact insights
            high_impact_insights = self.db.query(AnalyticsInsight).filter(
                AnalyticsInsight.impact_level.in_(["high", "critical"])
            ).count()
            
            # Get unread insights
            unread_insights = self.db.query(AnalyticsInsight).filter(
                AnalyticsInsight.status == "active"
            ).count()
            
            # Get recent insights
            recent_insights = self.db.query(AnalyticsInsight).order_by(
                AnalyticsInsight.generated_at.desc()
            ).limit(5).all()
            
            recent_insights_data = []
            for insight in recent_insights:
                recent_insights_data.append({
                    "id": insight.id,
                    "title": insight.title,
                    "type": insight.insight_type,
                    "category": insight.category,
                    "impact": insight.impact_level,
                    "confidence": insight.confidence_score,
                    "generated_at": insight.generated_at
                })
            
            return BIInsightsSummary(
                total_insights=total_insights,
                insights_by_type=insights_by_type,
                insights_by_category=insights_by_category,
                high_impact_insights=high_impact_insights,
                unread_insights=unread_insights,
                recent_insights=recent_insights_data
            )
            
        except Exception as e:
            logger.error(f"Error getting BI insights summary: {e}")
            raise
    
    def get_data_quality_summary(self) -> DataQualitySummary:
        """Get data quality summary"""
        try:
            # Get all active quality checks
            checks = self.db.query(DataQualityCheck).filter(
                DataQualityCheck.is_active == True
            ).all()
            
            if not checks:
                return DataQualitySummary(
                    overall_quality_score=0.0,
                    checks_performed=0,
                    issues_found=0,
                    issues_resolved=0,
                    quality_by_source={},
                    recent_checks=[]
                )
            
            # Calculate overall quality score
            total_quality = sum(check.quality_score or 0 for check in checks)
            overall_quality_score = total_quality / len(checks) if checks else 0
            
            # Get issues summary
            total_issues = sum(check.issues_found for check in checks)
            total_resolved = sum(check.issues_resolved for check in checks)
            
            # Get quality by source
            quality_by_source = {}
            for check in checks:
                if check.data_source not in quality_by_source:
                    quality_by_source[check.data_source] = []
                if check.quality_score:
                    quality_by_source[check.data_source].append(check.quality_score)
            
            # Calculate average quality per source
            for source in quality_by_source:
                scores = quality_by_source[source]
                quality_by_source[source] = sum(scores) / len(scores) if scores else 0
            
            # Get recent checks
            recent_checks = self.db.query(DataQualityResult).order_by(
                DataQualityResult.check_date.desc()
            ).limit(5).all()
            
            recent_checks_data = []
            for check in recent_checks:
                recent_checks_data.append({
                    "id": check.id,
                    "check_date": check.check_date,
                    "quality_score": check.quality_score,
                    "issues_found": check.records_with_issues,
                    "total_records": check.total_records_checked
                })
            
            return DataQualitySummary(
                overall_quality_score=overall_quality_score,
                checks_performed=len(checks),
                issues_found=total_issues,
                issues_resolved=total_resolved,
                quality_by_source=quality_by_source,
                recent_checks=recent_checks_data
            )
            
        except Exception as e:
            logger.error(f"Error getting data quality summary: {e}")
            raise
