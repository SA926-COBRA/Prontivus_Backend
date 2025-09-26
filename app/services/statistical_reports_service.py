import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from decimal import Decimal
import pandas as pd
import numpy as np
from io import BytesIO
import base64

from app.models.statistical_reports import (
    StatisticalReport, ReportTemplate, ReportGeneration, ReportMetric,
    ReportMetricValue, ReportDashboard, ReportAccessLog, ReportSchedule
)
from app.schemas.statistical_reports import (
    ReportSearchRequest, ReportGenerationRequest, ReportSummary,
    MetricCalculationRequest, DashboardDataRequest, ReportAnalytics
)

logger = logging.getLogger(__name__)

class StatisticalReportsService:
    """Service for Statistical Reports management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Report Management
    def create_report(self, report_data: dict, user_id: int) -> StatisticalReport:
        """Create a new statistical report"""
        try:
            report = StatisticalReport(
                **report_data,
                created_by=user_id
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            return report
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            raise
    
    def search_reports(self, request: ReportSearchRequest) -> List[StatisticalReport]:
        """Search reports with filters"""
        try:
            query = self.db.query(StatisticalReport)
            
            if request.report_name:
                query = query.filter(StatisticalReport.report_name.ilike(f"%{request.report_name}%"))
            
            if request.report_type:
                query = query.filter(StatisticalReport.report_type == request.report_type)
            
            if request.status:
                query = query.filter(StatisticalReport.status == request.status)
            
            if request.created_by:
                query = query.filter(StatisticalReport.created_by == request.created_by)
            
            if request.date_from:
                query = query.filter(StatisticalReport.created_at >= request.date_from)
            
            if request.date_to:
                query = query.filter(StatisticalReport.created_at <= request.date_to)
            
            reports = query.order_by(desc(StatisticalReport.created_at)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return reports
        except Exception as e:
            logger.error(f"Error searching reports: {e}")
            raise
    
    def generate_report(self, request: ReportGenerationRequest, user_id: int) -> ReportGeneration:
        """Generate a statistical report"""
        try:
            # Get report
            report = self.db.query(StatisticalReport).filter(
                StatisticalReport.id == request.report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Create generation record
            generation = ReportGeneration(
                report_id=request.report_id,
                generation_start=datetime.utcnow(),
                status="generating",
                parameters_used=request.parameters,
                filters_applied=request.filters,
                date_range_used={
                    "start": request.date_range_start.isoformat() if request.date_range_start else None,
                    "end": request.date_range_end.isoformat() if request.date_range_end else None
                },
                generated_by=user_id
            )
            
            self.db.add(generation)
            
            # Update report status
            report.status = "generating"
            report.generation_count += 1
            
            self.db.commit()
            self.db.refresh(generation)
            
            # Generate report data
            try:
                report_data = self._generate_report_data(report, request)
                file_path = self._create_report_file(report, report_data, request.format or report.report_format)
                
                # Update generation record
                generation.status = "completed"
                generation.generation_end = datetime.utcnow()
                generation.file_path = file_path
                generation.records_processed = len(report_data) if isinstance(report_data, list) else 1
                generation.generation_time_seconds = (generation.generation_end - generation.generation_start).total_seconds()
                
                # Update report
                report.status = "completed"
                report.last_generated = datetime.utcnow()
                report.file_path = file_path
                report.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
            except Exception as e:
                # Update generation record with error
                generation.status = "failed"
                generation.generation_end = datetime.utcnow()
                generation.error_message = str(e)
                generation.generation_time_seconds = (generation.generation_end - generation.generation_start).total_seconds()
                
                # Update report
                report.status = "failed"
                
                logger.error(f"Error generating report data: {e}")
            
            self.db.commit()
            self.db.refresh(generation)
            
            return generation
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def _generate_report_data(self, report: StatisticalReport, request: ReportGenerationRequest) -> Union[List[Dict], Dict]:
        """Generate report data based on configuration"""
        try:
            # Build query based on report configuration
            query = self._build_report_query(report, request)
            
            # Execute query
            result = self.db.execute(query)
            data = result.fetchall()
            
            # Convert to list of dictionaries
            columns = result.keys()
            report_data = [dict(zip(columns, row)) for row in data]
            
            # Apply additional processing if needed
            if report.parameters and 'aggregation' in report.parameters:
                report_data = self._apply_aggregation(report_data, report.parameters['aggregation'])
            
            return report_data
        except Exception as e:
            logger.error(f"Error generating report data: {e}")
            raise
    
    def _build_report_query(self, report: StatisticalReport, request: ReportGenerationRequest) -> text:
        """Build SQL query for report generation"""
        try:
            # Base query
            base_query = f"SELECT * FROM {report.data_source}"
            
            # Add filters
            filters = []
            
            # Date range filters
            if request.date_range_start:
                filters.append(f"created_at >= '{request.date_range_start}'")
            if request.date_range_end:
                filters.append(f"created_at <= '{request.date_range_end}'")
            
            # Report filters
            if report.query_filters:
                for key, value in report.query_filters.items():
                    if isinstance(value, str):
                        filters.append(f"{key} = '{value}'")
                    else:
                        filters.append(f"{key} = {value}")
            
            # Request filters
            if request.filters:
                for key, value in request.filters.items():
                    if isinstance(value, str):
                        filters.append(f"{key} = '{value}'")
                    else:
                        filters.append(f"{key} = {value}")
            
            # Build final query
            if filters:
                base_query += " WHERE " + " AND ".join(filters)
            
            # Add ordering
            base_query += " ORDER BY created_at DESC"
            
            return text(base_query)
        except Exception as e:
            logger.error(f"Error building report query: {e}")
            raise
    
    def _apply_aggregation(self, data: List[Dict], aggregation_config: Dict) -> List[Dict]:
        """Apply aggregation to report data"""
        try:
            df = pd.DataFrame(data)
            
            if 'group_by' in aggregation_config:
                group_by = aggregation_config['group_by']
                agg_functions = aggregation_config.get('functions', {})
                
                # Apply aggregation
                aggregated = df.groupby(group_by).agg(agg_functions).reset_index()
                
                return aggregated.to_dict('records')
            
            return data
        except Exception as e:
            logger.error(f"Error applying aggregation: {e}")
            return data
    
    def _create_report_file(self, report: StatisticalReport, data: Union[List[Dict], Dict], format: str) -> str:
        """Create report file in specified format"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{report.report_name}_{timestamp}.{format}"
            file_path = os.path.join(reports_dir, filename)
            
            if format == "pdf":
                self._create_pdf_report(report, data, file_path)
            elif format == "excel":
                self._create_excel_report(report, data, file_path)
            elif format == "csv":
                self._create_csv_report(report, data, file_path)
            elif format == "html":
                self._create_html_report(report, data, file_path)
            elif format == "json":
                self._create_json_report(report, data, file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return file_path
        except Exception as e:
            logger.error(f"Error creating report file: {e}")
            raise
    
    def _create_pdf_report(self, report: StatisticalReport, data: Union[List[Dict], Dict], file_path: str):
        """Create PDF report"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph(report.report_name, styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Description
            if report.description:
                desc = Paragraph(report.description, styles['Normal'])
                story.append(desc)
                story.append(Spacer(1, 12))
            
            # Data table
            if isinstance(data, list) and data:
                # Create table data
                table_data = []
                
                # Headers
                headers = list(data[0].keys())
                table_data.append(headers)
                
                # Data rows
                for row in data:
                    table_data.append([str(row.get(header, '')) for header in headers])
                
                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
            
            # Build PDF
            doc.build(story)
        except Exception as e:
            logger.error(f"Error creating PDF report: {e}")
            raise
    
    def _create_excel_report(self, report: StatisticalReport, data: Union[List[Dict], Dict], file_path: str):
        """Create Excel report"""
        try:
            import xlsxwriter
            
            workbook = xlsxwriter.Workbook(file_path)
            worksheet = workbook.add_worksheet(report.report_name[:31])  # Excel sheet name limit
            
            # Add title
            title_format = workbook.add_format({'bold': True, 'font_size': 16})
            worksheet.write('A1', report.report_name, title_format)
            
            # Add description
            if report.description:
                worksheet.write('A2', report.description)
            
            # Add data
            if isinstance(data, list) and data:
                # Headers
                headers = list(data[0].keys())
                for col, header in enumerate(headers):
                    worksheet.write(3, col, header)
                
                # Data rows
                for row_idx, row in enumerate(data):
                    for col_idx, header in enumerate(headers):
                        worksheet.write(3 + row_idx + 1, col_idx, row.get(header, ''))
            
            workbook.close()
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            raise
    
    def _create_csv_report(self, report: StatisticalReport, data: Union[List[Dict], Dict], file_path: str):
        """Create CSV report"""
        try:
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                # Single record
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error creating CSV report: {e}")
            raise
    
    def _create_html_report(self, report: StatisticalReport, data: Union[List[Dict], Dict], file_path: str):
        """Create HTML report"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report.report_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>{report.report_name}</h1>
                {f'<p>{report.description}</p>' if report.description else ''}
                <p>Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
            
            if isinstance(data, list) and data:
                html_content += "<table><tr>"
                headers = list(data[0].keys())
                for header in headers:
                    html_content += f"<th>{header}</th>"
                html_content += "</tr>"
                
                for row in data:
                    html_content += "<tr>"
                    for header in headers:
                        html_content += f"<td>{row.get(header, '')}</td>"
                    html_content += "</tr>"
                
                html_content += "</table>"
            
            html_content += "</body></html>"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            logger.error(f"Error creating HTML report: {e}")
            raise
    
    def _create_json_report(self, report: StatisticalReport, data: Union[List[Dict], Dict], file_path: str):
        """Create JSON report"""
        try:
            report_data = {
                "report_name": report.report_name,
                "description": report.description,
                "generated_at": datetime.utcnow().isoformat(),
                "data": data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error creating JSON report: {e}")
            raise
    
    # Metric Management
    def calculate_metric(self, request: MetricCalculationRequest) -> ReportMetricValue:
        """Calculate metric value for a specific period"""
        try:
            # Get metric
            metric = self.db.query(ReportMetric).filter(
                ReportMetric.id == request.metric_id
            ).first()
            
            if not metric:
                raise ValueError("Metric not found")
            
            # Calculate value
            value = self._calculate_metric_value(metric, request)
            
            # Get previous value for comparison
            previous_value = self._get_previous_metric_value(metric, request)
            
            # Calculate change percentage
            change_percentage = None
            if previous_value:
                change_percentage = ((value - previous_value) / previous_value) * 100
            
            # Determine trend direction
            trend_direction = None
            if change_percentage is not None:
                if change_percentage > 5:
                    trend_direction = "up"
                elif change_percentage < -5:
                    trend_direction = "down"
                else:
                    trend_direction = "stable"
            
            # Create metric value record
            metric_value = ReportMetricValue(
                metric_id=request.metric_id,
                value=value,
                period_start=request.period_start,
                period_end=request.period_end,
                period_type=request.period_type,
                previous_value=previous_value,
                change_percentage=change_percentage,
                trend_direction=trend_direction
            )
            
            self.db.add(metric_value)
            self.db.commit()
            self.db.refresh(metric_value)
            
            return metric_value
        except Exception as e:
            logger.error(f"Error calculating metric: {e}")
            raise
    
    def _calculate_metric_value(self, metric: ReportMetric, request: MetricCalculationRequest) -> Decimal:
        """Calculate metric value based on configuration"""
        try:
            if metric.calculation_query:
                # Use SQL query
                query = metric.calculation_query.format(
                    period_start=request.period_start,
                    period_end=request.period_end
                )
                result = self.db.execute(text(query))
                value = result.scalar()
                return Decimal(str(value)) if value else Decimal('0')
            
            elif metric.calculation_formula:
                # Use mathematical formula
                # This would need a more sophisticated formula parser
                # For now, return a placeholder value
                return Decimal('0')
            
            else:
                # Default calculation based on metric type
                if metric.metric_type == "count":
                    query = f"SELECT COUNT(*) FROM {metric.data_source} WHERE created_at BETWEEN '{request.period_start}' AND '{request.period_end}'"
                elif metric.metric_type == "sum":
                    query = f"SELECT SUM(amount) FROM {metric.data_source} WHERE created_at BETWEEN '{request.period_start}' AND '{request.period_end}'"
                elif metric.metric_type == "average":
                    query = f"SELECT AVG(amount) FROM {metric.data_source} WHERE created_at BETWEEN '{request.period_start}' AND '{request.period_end}'"
                else:
                    query = f"SELECT COUNT(*) FROM {metric.data_source} WHERE created_at BETWEEN '{request.period_start}' AND '{request.period_end}'"
                
                result = self.db.execute(text(query))
                value = result.scalar()
                return Decimal(str(value)) if value else Decimal('0')
        except Exception as e:
            logger.error(f"Error calculating metric value: {e}")
            return Decimal('0')
    
    def _get_previous_metric_value(self, metric: ReportMetric, request: MetricCalculationRequest) -> Optional[Decimal]:
        """Get previous metric value for comparison"""
        try:
            # Calculate previous period
            period_duration = request.period_end - request.period_start
            previous_period_start = request.period_start - period_duration
            previous_period_end = request.period_start
            
            # Get previous value
            previous_value = self.db.query(ReportMetricValue).filter(
                ReportMetricValue.metric_id == metric.id,
                ReportMetricValue.period_start == previous_period_start,
                ReportMetricValue.period_end == previous_period_end
            ).first()
            
            return previous_value.value if previous_value else None
        except Exception as e:
            logger.error(f"Error getting previous metric value: {e}")
            return None
    
    # Dashboard Management
    def get_dashboard_data(self, request: DashboardDataRequest) -> Dict[str, Any]:
        """Get dashboard data"""
        try:
            # Get dashboard
            dashboard = self.db.query(ReportDashboard).filter(
                ReportDashboard.id == request.dashboard_id
            ).first()
            
            if not dashboard:
                raise ValueError("Dashboard not found")
            
            # Get widget data
            widget_data = {}
            for widget_id, widget_config in dashboard.widgets.items():
                widget_data[widget_id] = self._get_widget_data(widget_config, request.filters)
            
            return {
                "dashboard_id": dashboard.id,
                "dashboard_name": dashboard.dashboard_name,
                "layout_config": dashboard.layout_config,
                "widgets": widget_data,
                "filters": dashboard.filters,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
    
    def _get_widget_data(self, widget_config: Dict, filters: Optional[Dict]) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            widget_type = widget_config.get('type')
            
            if widget_type == 'metric':
                return self._get_metric_widget_data(widget_config, filters)
            elif widget_type == 'chart':
                return self._get_chart_widget_data(widget_config, filters)
            elif widget_type == 'table':
                return self._get_table_widget_data(widget_config, filters)
            else:
                return {"error": f"Unknown widget type: {widget_type}"}
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {"error": str(e)}
    
    def _get_metric_widget_data(self, widget_config: Dict, filters: Optional[Dict]) -> Dict[str, Any]:
        """Get metric widget data"""
        try:
            metric_id = widget_config.get('metric_id')
            if not metric_id:
                return {"error": "Metric ID not specified"}
            
            # Get latest metric value
            metric_value = self.db.query(ReportMetricValue).filter(
                ReportMetricValue.metric_id == metric_id
            ).order_by(desc(ReportMetricValue.calculated_at)).first()
            
            if not metric_value:
                return {"value": 0, "trend": "stable", "change_percentage": 0}
            
            return {
                "value": float(metric_value.value),
                "trend": metric_value.trend_direction or "stable",
                "change_percentage": metric_value.change_percentage or 0,
                "period_start": metric_value.period_start.isoformat(),
                "period_end": metric_value.period_end.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting metric widget data: {e}")
            return {"error": str(e)}
    
    def _get_chart_widget_data(self, widget_config: Dict, filters: Optional[Dict]) -> Dict[str, Any]:
        """Get chart widget data"""
        try:
            data_source = widget_config.get('data_source')
            chart_type = widget_config.get('chart_type', 'line')
            
            # Build query
            query = f"SELECT * FROM {data_source}"
            
            # Add filters
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    query += " WHERE " + " AND ".join(filter_conditions)
            
            # Execute query
            result = self.db.execute(text(query))
            data = result.fetchall()
            
            # Convert to chart format
            columns = result.keys()
            chart_data = [dict(zip(columns, row)) for row in data]
            
            return {
                "type": chart_type,
                "data": chart_data,
                "labels": list(columns)
            }
        except Exception as e:
            logger.error(f"Error getting chart widget data: {e}")
            return {"error": str(e)}
    
    def _get_table_widget_data(self, widget_config: Dict, filters: Optional[Dict]) -> Dict[str, Any]:
        """Get table widget data"""
        try:
            data_source = widget_config.get('data_source')
            limit = widget_config.get('limit', 100)
            
            # Build query
            query = f"SELECT * FROM {data_source}"
            
            # Add filters
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    query += " WHERE " + " AND ".join(filter_conditions)
            
            # Add limit
            query += f" LIMIT {limit}"
            
            # Execute query
            result = self.db.execute(text(query))
            data = result.fetchall()
            
            # Convert to table format
            columns = result.keys()
            table_data = [dict(zip(columns, row)) for row in data]
            
            return {
                "columns": list(columns),
                "data": table_data,
                "total_rows": len(table_data)
            }
        except Exception as e:
            logger.error(f"Error getting table widget data: {e}")
            return {"error": str(e)}
    
    # Summary and Analytics
    def get_report_summary(self) -> ReportSummary:
        """Get report summary statistics"""
        try:
            total_reports = self.db.query(StatisticalReport).count()
            active_reports = self.db.query(StatisticalReport).filter(
                StatisticalReport.status == "completed"
            ).count()
            
            # Reports by type
            type_stats = self.db.query(
                StatisticalReport.report_type,
                func.count(StatisticalReport.id)
            ).group_by(StatisticalReport.report_type).all()
            
            reports_by_type = {
                stat[0].value: stat[1] for stat in type_stats
            }
            
            # Reports by status
            status_stats = self.db.query(
                StatisticalReport.status,
                func.count(StatisticalReport.id)
            ).group_by(StatisticalReport.status).all()
            
            reports_by_status = {
                stat[0].value: stat[1] for stat in status_stats
            }
            
            # Generation statistics
            total_generations = self.db.query(ReportGeneration).count()
            successful_generations = self.db.query(ReportGeneration).filter(
                ReportGeneration.status == "completed"
            ).count()
            failed_generations = self.db.query(ReportGeneration).filter(
                ReportGeneration.status == "failed"
            ).count()
            
            # Download statistics
            total_downloads = self.db.query(StatisticalReport).with_entities(
                func.sum(StatisticalReport.download_count)
            ).scalar() or 0
            
            return ReportSummary(
                total_reports=total_reports,
                active_reports=active_reports,
                reports_by_type=reports_by_type,
                reports_by_status=reports_by_status,
                total_generations=total_generations,
                successful_generations=successful_generations,
                failed_generations=failed_generations,
                total_downloads=total_downloads
            )
        except Exception as e:
            logger.error(f"Error getting report summary: {e}")
            raise
    
    def get_report_analytics(self) -> ReportAnalytics:
        """Get detailed report analytics"""
        try:
            # Basic statistics
            total_reports = self.db.query(StatisticalReport).count()
            
            # Time-based statistics
            today = date.today()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            reports_generated_today = self.db.query(ReportGeneration).filter(
                func.date(ReportGeneration.generation_start) == today
            ).count()
            
            reports_generated_this_week = self.db.query(ReportGeneration).filter(
                func.date(ReportGeneration.generation_start) >= week_ago
            ).count()
            
            reports_generated_this_month = self.db.query(ReportGeneration).filter(
                func.date(ReportGeneration.generation_start) >= month_ago
            ).count()
            
            # Most accessed reports
            most_accessed = self.db.query(StatisticalReport).order_by(
                desc(StatisticalReport.download_count)
            ).limit(5).all()
            
            most_accessed_reports = [
                {
                    "id": report.id,
                    "name": report.report_name,
                    "downloads": report.download_count,
                    "type": report.report_type.value
                }
                for report in most_accessed
            ]
            
            # Generation success rate
            total_generations = self.db.query(ReportGeneration).count()
            successful_generations = self.db.query(ReportGeneration).filter(
                ReportGeneration.status == "completed"
            ).count()
            
            generation_success_rate = (successful_generations / total_generations * 100) if total_generations > 0 else 0
            
            # Average generation time
            avg_generation_time = self.db.query(ReportGeneration).with_entities(
                func.avg(ReportGeneration.generation_time_seconds)
            ).filter(ReportGeneration.generation_time_seconds.isnot(None)).scalar() or 0
            
            # Top report types
            top_types = self.db.query(
                StatisticalReport.report_type,
                func.count(StatisticalReport.id)
            ).group_by(StatisticalReport.report_type).order_by(
                desc(func.count(StatisticalReport.id))
            ).limit(5).all()
            
            top_report_types = [
                {"type": stat[0].value, "count": stat[1]}
                for stat in top_types
            ]
            
            # User activity (simplified)
            user_activity = self.db.query(
                ReportGeneration.generated_by,
                func.count(ReportGeneration.id)
            ).filter(ReportGeneration.generated_by.isnot(None)).group_by(
                ReportGeneration.generated_by
            ).order_by(desc(func.count(ReportGeneration.id))).limit(10).all()
            
            user_activity_list = [
                {"user_id": stat[0], "generations": stat[1]}
                for stat in user_activity
            ]
            
            return ReportAnalytics(
                total_reports=total_reports,
                reports_generated_today=reports_generated_today,
                reports_generated_this_week=reports_generated_this_week,
                reports_generated_this_month=reports_generated_this_month,
                most_accessed_reports=most_accessed_reports,
                generation_success_rate=generation_success_rate,
                average_generation_time=avg_generation_time,
                top_report_types=top_report_types,
                user_activity=user_activity_list
            )
        except Exception as e:
            logger.error(f"Error getting report analytics: {e}")
            raise
