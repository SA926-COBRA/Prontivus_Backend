"""
Health Plan Integration Service Layer
Handles business logic for health plan API integrations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
import json
import logging
import httpx
import asyncio
from cryptography.fernet import Fernet

from app.models.health_plan_integration import (
    HealthPlanProvider, HealthPlanAPIEndpoint, HealthPlanConnectionLog,
    HealthPlanAuthorization, HealthPlanEligibility, HealthPlanConfiguration,
    IntegrationStatus, AuthMethod
)
from app.schemas.health_plan_integration import (
    HealthPlanProviderCreate, HealthPlanProviderUpdate, HealthPlanProviderInDB,
    HealthPlanAPIEndpointCreate, HealthPlanAPIEndpointUpdate, HealthPlanAPIEndpointInDB,
    HealthPlanAuthorizationCreate, HealthPlanAuthorizationUpdate, HealthPlanAuthorizationInDB,
    HealthPlanEligibilityCreate, HealthPlanEligibilityUpdate, HealthPlanEligibilityInDB,
    HealthPlanConnectionLogCreate, HealthPlanConnectionLogInDB,
    HealthPlanConfigurationCreate, HealthPlanConfigurationUpdate, HealthPlanConfigurationInDB,
    ConnectionTestRequest, ConnectionTestResponse, HealthPlanDashboardData,
    HealthPlanProviderSearch, HealthPlanAuthorizationSearch, HealthPlanEligibilitySearch
)

logger = logging.getLogger(__name__)


class HealthPlanIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like passwords and API keys"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    # Health Plan Provider Management
    def create_provider(self, provider_data: HealthPlanProviderCreate, user_id: int) -> HealthPlanProviderInDB:
        """Create a new health plan provider"""
        try:
            provider_dict = provider_data.dict()
            
            # Encrypt sensitive fields
            if provider_dict.get('client_secret'):
                provider_dict['client_secret'] = self._encrypt_sensitive_data(provider_dict['client_secret'])
            if provider_dict.get('api_key'):
                provider_dict['api_key'] = self._encrypt_sensitive_data(provider_dict['api_key'])
            if provider_dict.get('password'):
                provider_dict['password'] = self._encrypt_sensitive_data(provider_dict['password'])
            if provider_dict.get('bearer_token'):
                provider_dict['bearer_token'] = self._encrypt_sensitive_data(provider_dict['bearer_token'])
            
            provider_dict['created_by'] = user_id
            provider_dict['updated_by'] = user_id
            
            provider = HealthPlanProvider(**provider_dict)
            self.db.add(provider)
            self.db.commit()
            self.db.refresh(provider)
            return HealthPlanProviderInDB.from_orm(provider)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating health plan provider: {e}")
            raise

    def get_providers(self, search_params: HealthPlanProviderSearch, skip: int = 0, limit: int = 100) -> List[HealthPlanProviderInDB]:
        """Get health plan providers with search filters"""
        query = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.is_active == True)
        
        if search_params.name:
            query = query.filter(HealthPlanProvider.name.ilike(f"%{search_params.name}%"))
        if search_params.status:
            query = query.filter(HealthPlanProvider.status == search_params.status)
        if search_params.auth_method:
            query = query.filter(HealthPlanProvider.auth_method == search_params.auth_method)
        if search_params.supports_authorization is not None:
            query = query.filter(HealthPlanProvider.supports_authorization == search_params.supports_authorization)
        if search_params.supports_eligibility is not None:
            query = query.filter(HealthPlanProvider.supports_eligibility == search_params.supports_eligibility)
        if search_params.supports_sadt is not None:
            query = query.filter(HealthPlanProvider.supports_sadt == search_params.supports_sadt)
        
        providers = query.order_by(desc(HealthPlanProvider.created_at)).offset(skip).limit(limit).all()
        return [HealthPlanProviderInDB.from_orm(provider) for provider in providers]

    def get_provider_by_id(self, provider_id: int) -> Optional[HealthPlanProviderInDB]:
        """Get health plan provider by ID"""
        provider = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.id == provider_id).first()
        return HealthPlanProviderInDB.from_orm(provider) if provider else None

    def update_provider(self, provider_id: int, provider_data: HealthPlanProviderUpdate, user_id: int) -> Optional[HealthPlanProviderInDB]:
        """Update health plan provider"""
        provider = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.id == provider_id).first()
        if not provider:
            return None
        
        update_data = provider_data.dict(exclude_unset=True)
        
        # Encrypt sensitive fields if they're being updated
        if 'client_secret' in update_data and update_data['client_secret']:
            update_data['client_secret'] = self._encrypt_sensitive_data(update_data['client_secret'])
        if 'api_key' in update_data and update_data['api_key']:
            update_data['api_key'] = self._encrypt_sensitive_data(update_data['api_key'])
        if 'password' in update_data and update_data['password']:
            update_data['password'] = self._encrypt_sensitive_data(update_data['password'])
        if 'bearer_token' in update_data and update_data['bearer_token']:
            update_data['bearer_token'] = self._encrypt_sensitive_data(update_data['bearer_token'])
        
        for field, value in update_data.items():
            setattr(provider, field, value)
        
        provider.updated_by = user_id
        provider.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(provider)
        return HealthPlanProviderInDB.from_orm(provider)

    def delete_provider(self, provider_id: int) -> bool:
        """Soft delete health plan provider"""
        provider = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.id == provider_id).first()
        if not provider:
            return False
        
        provider.is_active = False
        provider.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # API Endpoint Management
    def create_endpoint(self, endpoint_data: HealthPlanAPIEndpointCreate) -> HealthPlanAPIEndpointInDB:
        """Create a new API endpoint"""
        try:
            endpoint = HealthPlanAPIEndpoint(**endpoint_data.dict())
            self.db.add(endpoint)
            self.db.commit()
            self.db.refresh(endpoint)
            return HealthPlanAPIEndpointInDB.from_orm(endpoint)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating API endpoint: {e}")
            raise

    def get_endpoints_by_provider(self, provider_id: int) -> List[HealthPlanAPIEndpointInDB]:
        """Get API endpoints for a provider"""
        endpoints = self.db.query(HealthPlanAPIEndpoint).filter(
            HealthPlanAPIEndpoint.provider_id == provider_id,
            HealthPlanAPIEndpoint.is_active == True
        ).all()
        return [HealthPlanAPIEndpointInDB.from_orm(endpoint) for endpoint in endpoints]

    def update_endpoint(self, endpoint_id: int, endpoint_data: HealthPlanAPIEndpointUpdate) -> Optional[HealthPlanAPIEndpointInDB]:
        """Update API endpoint"""
        endpoint = self.db.query(HealthPlanAPIEndpoint).filter(HealthPlanAPIEndpoint.id == endpoint_id).first()
        if not endpoint:
            return None
        
        update_data = endpoint_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(endpoint, field, value)
        
        endpoint.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(endpoint)
        return HealthPlanAPIEndpointInDB.from_orm(endpoint)

    # Connection Testing
    async def test_connection(self, test_request: ConnectionTestRequest) -> ConnectionTestResponse:
        """Test connection to health plan provider"""
        provider = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.id == test_request.provider_id).first()
        if not provider:
            return ConnectionTestResponse(success=False, error_message="Provider not found")
        
        try:
            # Update provider status to testing
            provider.status = IntegrationStatus.TESTING
            provider.last_connection_test = datetime.utcnow()
            self.db.commit()
            
            # Prepare request
            headers = {}
            auth_data = {}
            
            # Configure authentication based on method
            if provider.auth_method == AuthMethod.OAUTH2:
                # For OAuth2, we would typically get a token first
                # This is a simplified test - in production, implement full OAuth2 flow
                headers['Authorization'] = f"Bearer {provider.bearer_token or 'test-token'}"
            elif provider.auth_method == AuthMethod.API_KEY:
                api_key = self._decrypt_sensitive_data(provider.api_key) if provider.api_key else "test-key"
                headers[provider.api_key_header] = api_key
            elif provider.auth_method == AuthMethod.BASIC_AUTH:
                username = provider.username or "test-user"
                password = self._decrypt_sensitive_data(provider.password) if provider.password else "test-pass"
                auth_data = {"username": username, "password": password}
            elif provider.auth_method == AuthMethod.BEARER_TOKEN:
                token = self._decrypt_sensitive_data(provider.bearer_token) if provider.bearer_token else "test-token"
                headers['Authorization'] = f"Bearer {token}"
            
            # Make test request
            test_url = f"{provider.base_url}/health" if not test_request.endpoint_type else f"{provider.base_url}/{test_request.endpoint_type}"
            
            async with httpx.AsyncClient(timeout=provider.connection_timeout) as client:
                start_time = datetime.utcnow()
                
                if provider.auth_method == AuthMethod.BASIC_AUTH:
                    response = await client.get(test_url, headers=headers, auth=(auth_data["username"], auth_data["password"]))
                else:
                    response = await client.get(test_url, headers=headers)
                
                end_time = datetime.utcnow()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Log the connection attempt
                self._log_connection(provider.id, test_url, "GET", headers, None, 
                                   response.status_code, dict(response.headers), response.text, 
                                   response_time_ms, None, None, None, "connection_test")
                
                # Update provider status
                if response.status_code == 200:
                    provider.status = IntegrationStatus.ACTIVE
                    provider.last_connection_status = "success"
                    provider.last_error_message = None
                else:
                    provider.status = IntegrationStatus.ERROR
                    provider.last_connection_status = "error"
                    provider.last_error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                
                provider.last_connection_test = datetime.utcnow()
                self.db.commit()
                
                return ConnectionTestResponse(
                    success=response.status_code == 200,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    error_message=None if response.status_code == 200 else f"HTTP {response.status_code}",
                    response_data=response.json() if response.status_code == 200 else None
                )
                
        except Exception as e:
            logger.error(f"Error testing connection to provider {provider.id}: {e}")
            
            # Update provider status
            provider.status = IntegrationStatus.ERROR
            provider.last_connection_status = "error"
            provider.last_error_message = str(e)
            provider.last_connection_test = datetime.utcnow()
            self.db.commit()
            
            return ConnectionTestResponse(
                success=False,
                error_message=str(e)
            )

    def _log_connection(self, provider_id: int, url: str, method: str, headers: Dict, body: str,
                       status_code: int, response_headers: Dict, response_body: str,
                       response_time_ms: int, error_message: str, error_type: str,
                       user_id: int, request_type: str):
        """Log API connection details"""
        try:
            log_entry = HealthPlanConnectionLog(
                provider_id=provider_id,
                request_url=url,
                request_method=method,
                request_headers=headers,
                request_body=body,
                response_status_code=status_code,
                response_headers=response_headers,
                response_body=response_body[:1000] if response_body else None,  # Limit response body size
                response_time_ms=response_time_ms,
                error_message=error_message,
                error_type=error_type,
                user_id=user_id,
                request_type=request_type
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging connection: {e}")

    # Authorization Management
    def create_authorization(self, auth_data: HealthPlanAuthorizationCreate) -> HealthPlanAuthorizationInDB:
        """Create a new authorization request"""
        try:
            auth_dict = auth_data.dict()
            auth_dict['authorization_number'] = self._generate_authorization_number()
            
            authorization = HealthPlanAuthorization(**auth_dict)
            self.db.add(authorization)
            self.db.commit()
            self.db.refresh(authorization)
            return HealthPlanAuthorizationInDB.from_orm(authorization)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating authorization: {e}")
            raise

    def get_authorizations(self, search_params: HealthPlanAuthorizationSearch, skip: int = 0, limit: int = 100) -> List[HealthPlanAuthorizationInDB]:
        """Get authorization requests with search filters"""
        query = self.db.query(HealthPlanAuthorization)
        
        if search_params.provider_id:
            query = query.filter(HealthPlanAuthorization.provider_id == search_params.provider_id)
        if search_params.patient_id:
            query = query.filter(HealthPlanAuthorization.patient_id == search_params.patient_id)
        if search_params.doctor_id:
            query = query.filter(HealthPlanAuthorization.doctor_id == search_params.doctor_id)
        if search_params.status:
            query = query.filter(HealthPlanAuthorization.status == search_params.status)
        if search_params.date_from:
            query = query.filter(HealthPlanAuthorization.requested_date >= search_params.date_from)
        if search_params.date_to:
            query = query.filter(HealthPlanAuthorization.requested_date <= search_params.date_to)
        if search_params.urgency_level:
            query = query.filter(HealthPlanAuthorization.urgency_level == search_params.urgency_level)
        
        authorizations = query.order_by(desc(HealthPlanAuthorization.requested_date)).offset(skip).limit(limit).all()
        return [HealthPlanAuthorizationInDB.from_orm(auth) for auth in authorizations]

    def _generate_authorization_number(self) -> str:
        """Generate unique authorization number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"AUTH{timestamp}{random_suffix}"

    # Eligibility Management
    def create_eligibility_check(self, eligibility_data: HealthPlanEligibilityCreate) -> HealthPlanEligibilityInDB:
        """Create a new eligibility check"""
        try:
            eligibility_dict = eligibility_data.dict()
            eligibility_dict['eligibility_number'] = self._generate_eligibility_number()
            eligibility_dict['verification_date'] = datetime.utcnow()
            
            eligibility = HealthPlanEligibility(**eligibility_dict)
            self.db.add(eligibility)
            self.db.commit()
            self.db.refresh(eligibility)
            return HealthPlanEligibilityInDB.from_orm(eligibility)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating eligibility check: {e}")
            raise

    def get_eligibility_checks(self, search_params: HealthPlanEligibilitySearch, skip: int = 0, limit: int = 100) -> List[HealthPlanEligibilityInDB]:
        """Get eligibility checks with search filters"""
        query = self.db.query(HealthPlanEligibility)
        
        if search_params.provider_id:
            query = query.filter(HealthPlanEligibility.provider_id == search_params.provider_id)
        if search_params.patient_id:
            query = query.filter(HealthPlanEligibility.patient_id == search_params.patient_id)
        if search_params.is_eligible is not None:
            query = query.filter(HealthPlanEligibility.is_eligible == search_params.is_eligible)
        if search_params.date_from:
            query = query.filter(HealthPlanEligibility.verification_date >= search_params.date_from)
        if search_params.date_to:
            query = query.filter(HealthPlanEligibility.verification_date <= search_params.date_to)
        
        eligibility_checks = query.order_by(desc(HealthPlanEligibility.verification_date)).offset(skip).limit(limit).all()
        return [HealthPlanEligibilityInDB.from_orm(check) for check in eligibility_checks]

    def _generate_eligibility_number(self) -> str:
        """Generate unique eligibility number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"ELIG{timestamp}{random_suffix}"

    # Dashboard Data
    def get_dashboard_data(self) -> HealthPlanDashboardData:
        """Get dashboard data for health plan integrations"""
        try:
            # Provider statistics
            total_providers = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.is_active == True).count()
            active_providers = self.db.query(HealthPlanProvider).filter(
                HealthPlanProvider.is_active == True,
                HealthPlanProvider.status == IntegrationStatus.ACTIVE
            ).count()
            inactive_providers = self.db.query(HealthPlanProvider).filter(
                HealthPlanProvider.is_active == True,
                HealthPlanProvider.status == IntegrationStatus.INACTIVE
            ).count()
            error_providers = self.db.query(HealthPlanProvider).filter(
                HealthPlanProvider.is_active == True,
                HealthPlanProvider.status == IntegrationStatus.ERROR
            ).count()
            
            # Request statistics for today
            today = datetime.utcnow().date()
            total_requests_today = self.db.query(HealthPlanConnectionLog).filter(
                HealthPlanConnectionLog.timestamp >= today
            ).count()
            
            successful_requests_today = self.db.query(HealthPlanConnectionLog).filter(
                HealthPlanConnectionLog.timestamp >= today,
                HealthPlanConnectionLog.response_status_code == 200
            ).count()
            
            failed_requests_today = self.db.query(HealthPlanConnectionLog).filter(
                HealthPlanConnectionLog.timestamp >= today,
                HealthPlanConnectionLog.response_status_code != 200
            ).count()
            
            # Average response time
            avg_response_time = self.db.query(HealthPlanConnectionLog).filter(
                HealthPlanConnectionLog.timestamp >= today,
                HealthPlanConnectionLog.response_time_ms.isnot(None)
            ).with_entities(HealthPlanConnectionLog.response_time_ms).all()
            
            average_response_time_ms = sum([r[0] for r in avg_response_time]) / len(avg_response_time) if avg_response_time else 0
            
            # Recent errors
            recent_errors = self.db.query(HealthPlanConnectionLog).filter(
                HealthPlanConnectionLog.error_message.isnot(None)
            ).order_by(desc(HealthPlanConnectionLog.timestamp)).limit(5).all()
            
            recent_errors_data = [
                {
                    "provider_id": log.provider_id,
                    "error_message": log.error_message,
                    "timestamp": log.timestamp.isoformat(),
                    "request_type": log.request_type
                }
                for log in recent_errors
            ]
            
            # Provider status
            providers = self.db.query(HealthPlanProvider).filter(HealthPlanProvider.is_active == True).all()
            provider_status = [
                {
                    "id": provider.id,
                    "name": provider.name,
                    "status": provider.status.value,
                    "last_connection_test": provider.last_connection_test.isoformat() if provider.last_connection_test else None,
                    "last_connection_status": provider.last_connection_status
                }
                for provider in providers
            ]
            
            return HealthPlanDashboardData(
                total_providers=total_providers,
                active_providers=active_providers,
                inactive_providers=inactive_providers,
                error_providers=error_providers,
                total_requests_today=total_requests_today,
                successful_requests_today=successful_requests_today,
                failed_requests_today=failed_requests_today,
                average_response_time_ms=average_response_time_ms,
                recent_errors=recent_errors_data,
                provider_status=provider_status
            )
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
