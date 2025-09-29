import os
import json
import logging
import asyncio
import aiohttp
import httpx
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from decimal import Decimal
import uuid
import base64
import hashlib
import hmac

from app.models.integrations import (
    HealthPlanIntegration, TelemedicineIntegration,
    IntegrationSyncLog, IntegrationWebhook,
    WebhookLog, IntegrationHealthCheck
)
from app.models.health_plan_integration import HealthPlanAuthorization
from app.schemas.integrations import (
    IntegrationSearchRequest,
    AuthorizationSearchRequest, IntegrationSyncRequest,
    AuthorizationRequest,
    IntegrationSummary, IntegrationAnalytics
)

logger = logging.getLogger(__name__)

class IntegrationsService:
    """Service for Health Plans and Telemedicine integrations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Health Plan Integration Management
    def create_health_plan_integration(self, integration_data: dict, user_id: int) -> HealthPlanIntegration:
        """Create a new health plan integration"""
        try:
            integration = HealthPlanIntegration(
                **integration_data,
                created_by=user_id
            )
            
            self.db.add(integration)
            self.db.commit()
            self.db.refresh(integration)
            
            return integration
        except Exception as e:
            logger.error(f"Error creating health plan integration: {e}")
            raise
    
    def search_health_plan_integrations(self, request: IntegrationSearchRequest) -> List[HealthPlanIntegration]:
        """Search health plan integrations with filters"""
        try:
            query = self.db.query(HealthPlanIntegration)
            
            if request.integration_name:
                query = query.filter(HealthPlanIntegration.integration_name.ilike(f"%{request.integration_name}%"))
            
            if request.integration_type:
                query = query.filter(HealthPlanIntegration.integration_type == request.integration_type)
            
            if request.status:
                query = query.filter(HealthPlanIntegration.status == request.status)
            
            if request.created_by:
                query = query.filter(HealthPlanIntegration.created_by == request.created_by)
            
            if request.date_from:
                query = query.filter(HealthPlanIntegration.created_at >= request.date_from)
            
            if request.date_to:
                query = query.filter(HealthPlanIntegration.created_at <= request.date_to)
            
            integrations = query.order_by(desc(HealthPlanIntegration.created_at)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return integrations
        except Exception as e:
            logger.error(f"Error searching health plan integrations: {e}")
            raise
    
    def test_health_plan_integration(self, integration_id: int) -> Dict[str, Any]:
        """Test health plan integration connectivity"""
        try:
            integration = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            # Test connectivity
            test_result = self._test_integration_connectivity(integration)
            
            # Update integration status
            if test_result['success']:
                integration.status = "active"
                integration.last_success = datetime.utcnow()
                integration.last_error = None
                integration.error_count = 0
            else:
                integration.status = "error"
                integration.last_error = test_result['error']
                integration.error_count += 1
            
            self.db.commit()
            
            return test_result
        except Exception as e:
            logger.error(f"Error testing health plan integration: {e}")
            raise
    
    def sync_health_plan_data(self, request: IntegrationSyncRequest) -> IntegrationSyncLog:
        """Sync data with health plan integration"""
        try:
            integration = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.id == request.integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            # Create sync log
            sync_log = IntegrationSyncLog(
                integration_id=request.integration_id,
                sync_type=request.sync_type,
                sync_start=datetime.utcnow(),
                status="running"
            )
            
            self.db.add(sync_log)
            self.db.commit()
            self.db.refresh(sync_log)
            
            # Perform sync
            try:
                sync_result = self._perform_health_plan_sync(integration, request)
                
                # Update sync log
                sync_log.status = "completed"
                sync_log.sync_end = datetime.utcnow()
                sync_log.records_processed = sync_result.get('records_processed', 0)
                sync_log.records_created = sync_result.get('records_created', 0)
                sync_log.records_updated = sync_result.get('records_updated', 0)
                sync_log.records_failed = sync_result.get('records_failed', 0)
                sync_log.sync_data = sync_result
                
                # Update integration
                integration.last_sync = datetime.utcnow()
                integration.last_success = datetime.utcnow()
                integration.last_error = None
                integration.error_count = 0
                
            except Exception as e:
                # Update sync log with error
                sync_log.status = "failed"
                sync_log.sync_end = datetime.utcnow()
                sync_log.error_message = str(e)
                
                # Update integration
                integration.last_error = str(e)
                integration.error_count += 1
                
                logger.error(f"Error during health plan sync: {e}")
            
            self.db.commit()
            self.db.refresh(sync_log)
            
            return sync_log
        except Exception as e:
            logger.error(f"Error syncing health plan data: {e}")
            raise
    
    # Telemedicine Integration Management
    def create_telemedicine_integration(self, integration_data: dict, user_id: int) -> TelemedicineIntegration:
        """Create a new telemedicine integration"""
        try:
            integration = TelemedicineIntegration(
                **integration_data,
                created_by=user_id
            )
            
            self.db.add(integration)
            self.db.commit()
            self.db.refresh(integration)
            
            return integration
        except Exception as e:
            logger.error(f"Error creating telemedicine integration: {e}")
            raise
    
    def search_telemedicine_integrations(self, request: IntegrationSearchRequest) -> List[TelemedicineIntegration]:
        """Search telemedicine integrations with filters"""
        try:
            query = self.db.query(TelemedicineIntegration)
            
            if request.integration_name:
                query = query.filter(TelemedicineIntegration.integration_name.ilike(f"%{request.integration_name}%"))
            
            if request.provider:
                query = query.filter(TelemedicineIntegration.provider == request.provider)
            
            if request.status:
                query = query.filter(TelemedicineIntegration.status == request.status)
            
            if request.created_by:
                query = query.filter(TelemedicineIntegration.created_by == request.created_by)
            
            if request.date_from:
                query = query.filter(TelemedicineIntegration.created_at >= request.date_from)
            
            if request.date_to:
                query = query.filter(TelemedicineIntegration.created_at <= request.date_to)
            
            integrations = query.order_by(desc(TelemedicineIntegration.created_at)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return integrations
        except Exception as e:
            logger.error(f"Error searching telemedicine integrations: {e}")
            raise
    
    def test_telemedicine_integration(self, integration_id: int) -> Dict[str, Any]:
        """Test telemedicine integration connectivity"""
        try:
            integration = self.db.query(TelemedicineIntegration).filter(
                TelemedicineIntegration.id == integration_id
            ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            # Test connectivity
            test_result = self._test_integration_connectivity(integration)
            
            # Update integration status
            if test_result['success']:
                integration.status = "active"
                integration.last_success = datetime.utcnow()
                integration.last_error = None
                integration.error_count = 0
            else:
                integration.status = "error"
                integration.last_error = test_result['error']
                integration.error_count += 1
            
            self.db.commit()
            
            return test_result
        except Exception as e:
            logger.error(f"Error testing telemedicine integration: {e}")
            raise
    
    # Health Plan Authorization Management
    def create_authorization_request(self, request: AuthorizationRequest, user_id: int) -> HealthPlanAuthorization:
        """Create a new health plan authorization request"""
        try:
            # Generate authorization number
            authorization_number = self._generate_authorization_number()
            
            # Create authorization
            authorization = HealthPlanAuthorization(
                authorization_number=authorization_number,
                integration_id=request.integration_id,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                procedure_id=request.procedure_id,
                procedure_code=request.procedure_code,
                procedure_description=request.procedure_description,
                requested_date=request.requested_date,
                urgency_level=request.urgency_level,
                request_data={},
                created_by=user_id
            )
            
            self.db.add(authorization)
            self.db.commit()
            self.db.refresh(authorization)
            
            # Send authorization request to health plan
            try:
                request_result = self._send_authorization_request(authorization)
                
                # Update authorization with request data
                authorization.request_data = request_result.get('request_data', {})
                authorization.request_sent_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(authorization)
                
            except Exception as e:
                logger.error(f"Error sending authorization request: {e}")
                authorization.status = "error"
                authorization.error_message = str(e)
                self.db.commit()
            
            return authorization
        except Exception as e:
            logger.error(f"Error creating authorization request: {e}")
            raise
    
    def search_authorizations(self, request: AuthorizationSearchRequest) -> List[HealthPlanAuthorization]:
        """Search health plan authorizations with filters"""
        try:
            query = self.db.query(HealthPlanAuthorization)
            
            if request.integration_id:
                query = query.filter(HealthPlanAuthorization.integration_id == request.integration_id)
            
            if request.patient_id:
                query = query.filter(HealthPlanAuthorization.patient_id == request.patient_id)
            
            if request.doctor_id:
                query = query.filter(HealthPlanAuthorization.doctor_id == request.doctor_id)
            
            if request.authorization_status:
                query = query.filter(HealthPlanAuthorization.authorization_status == request.authorization_status)
            
            if request.procedure_code:
                query = query.filter(HealthPlanAuthorization.procedure_code.ilike(f"%{request.procedure_code}%"))
            
            if request.date_from:
                query = query.filter(HealthPlanAuthorization.requested_date >= request.date_from)
            
            if request.date_to:
                query = query.filter(HealthPlanAuthorization.requested_date <= request.date_to)
            
            authorizations = query.order_by(desc(HealthPlanAuthorization.created_at)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return authorizations
        except Exception as e:
            logger.error(f"Error searching authorizations: {e}")
            raise
    
    # Webhook Management
    def create_webhook(self, webhook_data: dict, user_id: int) -> IntegrationWebhook:
        """Create a new integration webhook"""
        try:
            webhook = IntegrationWebhook(
                **webhook_data,
                created_by=user_id
            )
            
            self.db.add(webhook)
            self.db.commit()
            self.db.refresh(webhook)
            
            return webhook
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise
    
    def process_webhook(self, webhook_id: int, event_data: dict) -> WebhookLog:
        """Process a webhook event"""
        try:
            webhook = self.db.query(IntegrationWebhook).filter(
                IntegrationWebhook.id == webhook_id
            ).first()
            
            if not webhook:
                raise ValueError("Webhook not found")
            
            # Create webhook log
            webhook_log = WebhookLog(
                webhook_id=webhook_id,
                request_url=webhook.webhook_url,
                request_method="POST",
                request_body=json.dumps(event_data),
                event_data=event_data
            )
            
            self.db.add(webhook_log)
            
            # Process webhook
            try:
                result = self._execute_webhook(webhook, event_data)
                
                # Update webhook log
                webhook_log.success = True
                webhook_log.response_status = result.get('status_code')
                webhook_log.response_body = result.get('response_body')
                webhook_log.response_time_ms = result.get('response_time_ms')
                
                # Update webhook statistics
                webhook.last_triggered = datetime.utcnow()
                webhook.success_count += 1
                
            except Exception as e:
                # Update webhook log with error
                webhook_log.success = False
                webhook_log.error_message = str(e)
                
                # Update webhook statistics
                webhook.last_triggered = datetime.utcnow()
                webhook.failure_count += 1
                webhook.last_error = str(e)
                
                logger.error(f"Error executing webhook: {e}")
            
            self.db.commit()
            self.db.refresh(webhook_log)
            
            return webhook_log
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise
    
    # Health Check Management
    def perform_health_check(self, integration_id: int, check_type: str = "connectivity") -> IntegrationHealthCheck:
        """Perform health check on integration"""
        try:
            # Get integration
            integration = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.id == integration_id
            ).first()
            
            if not integration:
                # Try telemedicine integration
                integration = self.db.query(TelemedicineIntegration).filter(
                    TelemedicineIntegration.id == integration_id
                ).first()
            
            if not integration:
                raise ValueError("Integration not found")
            
            # Create health check record
            health_check = IntegrationHealthCheck(
                integration_id=integration_id if hasattr(integration, 'id') else None,
                telemedicine_integration_id=integration_id if hasattr(integration, 'provider') else None,
                check_type=check_type,
                check_start=datetime.utcnow()
            )
            
            self.db.add(health_check)
            
            # Perform health check
            try:
                check_result = self._perform_health_check(integration, check_type)
                
                # Update health check record
                health_check.check_end = datetime.utcnow()
                health_check.status = check_result['status']
                health_check.response_time_ms = check_result.get('response_time_ms')
                health_check.error_message = check_result.get('error_message')
                health_check.metrics = check_result.get('metrics')
                health_check.details = check_result.get('details')
                
            except Exception as e:
                # Update health check record with error
                health_check.check_end = datetime.utcnow()
                health_check.status = "unhealthy"
                health_check.error_message = str(e)
                
                logger.error(f"Error during health check: {e}")
            
            self.db.commit()
            self.db.refresh(health_check)
            
            return health_check
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            raise
    
    # Summary and Analytics
    def get_integration_summary(self) -> IntegrationSummary:
        """Get integration summary statistics"""
        try:
            # Health plan integrations
            total_health_plan = self.db.query(HealthPlanIntegration).count()
            active_health_plan = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.status == "active"
            ).count()
            
            # Telemedicine integrations
            total_telemedicine = self.db.query(TelemedicineIntegration).count()
            active_telemedicine = self.db.query(TelemedicineIntegration).filter(
                TelemedicineIntegration.status == "active"
            ).count()
            
            # Total integrations
            total_integrations = total_health_plan + total_telemedicine
            active_integrations = active_health_plan + active_telemedicine
            
            # Integrations by status
            health_plan_status = self.db.query(
                HealthPlanIntegration.status,
                func.count(HealthPlanIntegration.id)
            ).group_by(HealthPlanIntegration.status).all()
            
            telemedicine_status = self.db.query(
                TelemedicineIntegration.status,
                func.count(TelemedicineIntegration.id)
            ).group_by(TelemedicineIntegration.status).all()
            
            integrations_by_status = {}
            for stat in health_plan_status:
                integrations_by_status[stat[0].value] = integrations_by_status.get(stat[0].value, 0) + stat[1]
            for stat in telemedicine_status:
                integrations_by_status[stat[0].value] = integrations_by_status.get(stat[0].value, 0) + stat[1]
            
            # Integrations by type
            integrations_by_type = {
                "health_plan": total_health_plan,
                "telemedicine": total_telemedicine
            }
            
            # Sessions (removed - handled by dedicated telemedicine service)
            
            # Authorizations
            total_authorizations = self.db.query(HealthPlanAuthorization).count()
            pending_authorizations = self.db.query(HealthPlanAuthorization).filter(
                HealthPlanAuthorization.authorization_status == "pending"
            ).count()
            
            return IntegrationSummary(
                total_integrations=total_integrations,
                active_integrations=active_integrations,
                health_plan_integrations=total_health_plan,
                telemedicine_integrations=total_telemedicine,
                integrations_by_status=integrations_by_status,
                integrations_by_type=integrations_by_type,
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                total_authorizations=total_authorizations,
                pending_authorizations=pending_authorizations
            )
        except Exception as e:
            logger.error(f"Error getting integration summary: {e}")
            raise
    
    def get_integration_analytics(self) -> IntegrationAnalytics:
        """Get detailed integration analytics"""
        try:
            # Basic statistics
            total_integrations = self.db.query(HealthPlanIntegration).count() + self.db.query(TelemedicineIntegration).count()
            active_integrations = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.status == "active"
            ).count() + self.db.query(TelemedicineIntegration).filter(
                TelemedicineIntegration.status == "active"
            ).count()
            
            failed_integrations = self.db.query(HealthPlanIntegration).filter(
                HealthPlanIntegration.status == "error"
            ).count() + self.db.query(TelemedicineIntegration).filter(
                TelemedicineIntegration.status == "error"
            ).count()
            
            # Integrations by provider
            telemedicine_providers = self.db.query(
                TelemedicineIntegration.provider,
                func.count(TelemedicineIntegration.id)
            ).group_by(TelemedicineIntegration.provider).all()
            
            integrations_by_provider = {
                stat[0].value: stat[1] for stat in telemedicine_providers
            }
            
            # Session statistics (removed - handled by dedicated telemedicine service)
            session_statistics = {}
            
            # Authorization statistics
            auth_stats = self.db.query(
                HealthPlanAuthorization.authorization_status,
                func.count(HealthPlanAuthorization.id)
            ).group_by(HealthPlanAuthorization.authorization_status).all()
            
            authorization_statistics = {
                stat[0]: stat[1] for stat in auth_stats
            }
            
            # Sync statistics
            sync_stats = self.db.query(
                IntegrationSyncLog.status,
                func.count(IntegrationSyncLog.id)
            ).group_by(IntegrationSyncLog.status).all()
            
            sync_statistics = {
                stat[0]: stat[1] for stat in sync_stats
            }
            
            # Webhook statistics
            webhook_stats = self.db.query(IntegrationWebhook).with_entities(
                func.count(IntegrationWebhook.id),
                func.sum(IntegrationWebhook.success_count),
                func.sum(IntegrationWebhook.failure_count)
            ).first()
            
            webhook_statistics = {
                "total_webhooks": webhook_stats[0] or 0,
                "total_successes": webhook_stats[1] or 0,
                "total_failures": webhook_stats[2] or 0
            }
            
            # Health check results
            health_check_stats = self.db.query(
                IntegrationHealthCheck.status,
                func.count(IntegrationHealthCheck.id)
            ).group_by(IntegrationHealthCheck.status).all()
            
            health_check_results = {
                stat[0]: stat[1] for stat in health_check_stats
            }
            
            # Performance metrics
            avg_response_time = self.db.query(IntegrationHealthCheck).with_entities(
                func.avg(IntegrationHealthCheck.response_time_ms)
            ).filter(IntegrationHealthCheck.response_time_ms.isnot(None)).scalar() or 0
            
            performance_metrics = {
                "average_response_time_ms": float(avg_response_time),
                "success_rate": (active_integrations / total_integrations * 100) if total_integrations > 0 else 0
            }
            
            return IntegrationAnalytics(
                total_integrations=total_integrations,
                active_integrations=active_integrations,
                failed_integrations=failed_integrations,
                integrations_by_provider=integrations_by_provider,
                session_statistics=session_statistics,
                authorization_statistics=authorization_statistics,
                sync_statistics=sync_statistics,
                webhook_statistics=webhook_statistics,
                health_check_results=health_check_results,
                performance_metrics=performance_metrics
            )
        except Exception as e:
            logger.error(f"Error getting integration analytics: {e}")
            raise
    
    # Private helper methods
    def _test_integration_connectivity(self, integration) -> Dict[str, Any]:
        """Test integration connectivity"""
        try:
            # Mock connectivity test
            # In real implementation, this would make actual API calls
            
            return {
                "success": True,
                "response_time_ms": 150,
                "status_code": 200,
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": None,
                "status_code": None
            }
    
    def _perform_health_plan_sync(self, integration: HealthPlanIntegration, request: IntegrationSyncRequest) -> Dict[str, Any]:
        """Perform health plan data synchronization"""
        try:
            # Mock sync operation
            # In real implementation, this would sync data with health plan API
            
            return {
                "records_processed": 100,
                "records_created": 10,
                "records_updated": 5,
                "records_failed": 0,
                "sync_duration_seconds": 30
            }
        except Exception as e:
            logger.error(f"Error during health plan sync: {e}")
            raise
    
    # Helper methods for integrations
    
    def _send_authorization_request(self, authorization: HealthPlanAuthorization) -> Dict[str, Any]:
        """Send authorization request to health plan"""
        try:
            # Mock authorization request
            # In real implementation, this would send request via health plan API
            
            return {
                "request_data": {
                    "authorization_number": authorization.authorization_number,
                    "procedure_code": authorization.procedure_code,
                    "patient_id": authorization.patient_id,
                    "requested_date": authorization.requested_date.isoformat()
                },
                "status": "submitted"
            }
        except Exception as e:
            logger.error(f"Error sending authorization request: {e}")
            raise
    
    def _execute_webhook(self, webhook: IntegrationWebhook, event_data: dict) -> Dict[str, Any]:
        """Execute webhook"""
        try:
            # Mock webhook execution
            # In real implementation, this would make HTTP request to webhook URL
            
            return {
                "status_code": 200,
                "response_body": "OK",
                "response_time_ms": 250
            }
        except Exception as e:
            logger.error(f"Error executing webhook: {e}")
            raise
    
    def _perform_health_check(self, integration, check_type: str) -> Dict[str, Any]:
        """Perform health check on integration"""
        try:
            # Mock health check
            # In real implementation, this would perform actual health checks
            
            return {
                "status": "healthy",
                "response_time_ms": 120,
                "metrics": {
                    "uptime": "99.9%",
                    "response_time": "120ms"
                },
                "details": {
                    "check_type": check_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            raise
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"TM{timestamp}{random_part}"
    
    def _generate_authorization_number(self) -> str:
        """Generate unique authorization number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"AUTH{timestamp}{random_part}"
