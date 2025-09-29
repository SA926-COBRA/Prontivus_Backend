"""
Health Plan Integration API Endpoints
Centralized panel for managing all provider APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.database import get_db
from app.services.health_plan_integration_service import HealthPlanIntegrationService
from app.services.auth_service import AuthService
from app.schemas.health_plan_integration import (
    HealthPlanProviderCreate, HealthPlanProviderUpdate, HealthPlanProviderInDB,
    HealthPlanAPIEndpointCreate, HealthPlanAPIEndpointUpdate, HealthPlanAPIEndpointInDB,
    HealthPlanAuthorizationCreate, HealthPlanAuthorizationUpdate, HealthPlanAuthorizationInDB,
    HealthPlanEligibilityCreate, HealthPlanEligibilityUpdate, HealthPlanEligibilityInDB,
    HealthPlanConnectionLogInDB, HealthPlanConfigurationCreate, HealthPlanConfigurationUpdate,
    HealthPlanConfigurationInDB, ConnectionTestRequest, ConnectionTestResponse,
    HealthPlanDashboardData, HealthPlanProviderSearch, HealthPlanAuthorizationSearch,
    HealthPlanEligibilitySearch, IntegrationStatus, AuthMethod
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Health Plan Provider Endpoints
@router.post("/providers", response_model=HealthPlanProviderInDB)
async def create_provider(
    provider_data: HealthPlanProviderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new health plan provider"""
    try:
        service = HealthPlanIntegrationService(db)
        return service.create_provider(provider_data, current_user.id)
    except Exception as e:
        logger.error(f"Error creating health plan provider: {e}")
        raise HTTPException(status_code=500, detail="Error creating health plan provider")


@router.get("/providers", response_model=List[HealthPlanProviderInDB])
async def get_providers(
    name: Optional[str] = None,
    status: Optional[IntegrationStatus] = None,
    auth_method: Optional[AuthMethod] = None,
    supports_authorization: Optional[bool] = None,
    supports_eligibility: Optional[bool] = None,
    supports_sadt: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get health plan providers with search filters"""
    try:
        search_params = HealthPlanProviderSearch(
            name=name,
            status=status,
            auth_method=auth_method,
            supports_authorization=supports_authorization,
            supports_eligibility=supports_eligibility,
            supports_sadt=supports_sadt
        )
        
        service = HealthPlanIntegrationService(db)
        return service.get_providers(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting health plan providers: {e}")
        raise HTTPException(status_code=500, detail="Error getting health plan providers")


@router.get("/providers/{provider_id}", response_model=HealthPlanProviderInDB)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get health plan provider by ID"""
    try:
        service = HealthPlanIntegrationService(db)
        provider = service.get_provider_by_id(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Health plan provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health plan provider: {e}")
        raise HTTPException(status_code=500, detail="Error getting health plan provider")


@router.put("/providers/{provider_id}", response_model=HealthPlanProviderInDB)
async def update_provider(
    provider_id: int,
    provider_data: HealthPlanProviderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Update health plan provider"""
    try:
        service = HealthPlanIntegrationService(db)
        provider = service.update_provider(provider_id, provider_data, current_user.id)
        if not provider:
            raise HTTPException(status_code=404, detail="Health plan provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating health plan provider: {e}")
        raise HTTPException(status_code=500, detail="Error updating health plan provider")


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Delete health plan provider"""
    try:
        service = HealthPlanIntegrationService(db)
        success = service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Health plan provider not found")
        return {"message": "Health plan provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting health plan provider: {e}")
        raise HTTPException(status_code=500, detail="Error deleting health plan provider")


# API Endpoint Management
@router.post("/providers/{provider_id}/endpoints", response_model=HealthPlanAPIEndpointInDB)
async def create_endpoint(
    provider_id: int,
    endpoint_data: HealthPlanAPIEndpointCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new API endpoint for a provider"""
    try:
        endpoint_data.provider_id = provider_id
        service = HealthPlanIntegrationService(db)
        return service.create_endpoint(endpoint_data)
    except Exception as e:
        logger.error(f"Error creating API endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error creating API endpoint")


@router.get("/providers/{provider_id}/endpoints", response_model=List[HealthPlanAPIEndpointInDB])
async def get_provider_endpoints(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get API endpoints for a provider"""
    try:
        service = HealthPlanIntegrationService(db)
        return service.get_endpoints_by_provider(provider_id)
    except Exception as e:
        logger.error(f"Error getting provider endpoints: {e}")
        raise HTTPException(status_code=500, detail="Error getting provider endpoints")


@router.put("/endpoints/{endpoint_id}", response_model=HealthPlanAPIEndpointInDB)
async def update_endpoint(
    endpoint_id: int,
    endpoint_data: HealthPlanAPIEndpointUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Update API endpoint"""
    try:
        service = HealthPlanIntegrationService(db)
        endpoint = service.update_endpoint(endpoint_id, endpoint_data)
        if not endpoint:
            raise HTTPException(status_code=404, detail="API endpoint not found")
        return endpoint
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error updating API endpoint")


# Connection Testing
@router.post("/providers/{provider_id}/test-connection", response_model=ConnectionTestResponse)
async def test_provider_connection(
    provider_id: int,
    endpoint_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Test connection to health plan provider"""
    try:
        test_request = ConnectionTestRequest(
            provider_id=provider_id,
            endpoint_type=endpoint_type
        )
        
        service = HealthPlanIntegrationService(db)
        return await service.test_connection(test_request)
    except Exception as e:
        logger.error(f"Error testing provider connection: {e}")
        raise HTTPException(status_code=500, detail="Error testing provider connection")


# Authorization Management
@router.post("/authorizations", response_model=HealthPlanAuthorizationInDB)
async def create_authorization(
    auth_data: HealthPlanAuthorizationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new authorization request"""
    try:
        service = HealthPlanIntegrationService(db)
        return service.create_authorization(auth_data)
    except Exception as e:
        logger.error(f"Error creating authorization: {e}")
        raise HTTPException(status_code=500, detail="Error creating authorization")


@router.get("/authorizations", response_model=List[HealthPlanAuthorizationInDB])
async def get_authorizations(
    provider_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    urgency_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get authorization requests with search filters"""
    try:
        search_params = HealthPlanAuthorizationSearch(
            provider_id=provider_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            urgency_level=urgency_level
        )
        
        service = HealthPlanIntegrationService(db)
        return service.get_authorizations(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting authorizations: {e}")
        raise HTTPException(status_code=500, detail="Error getting authorizations")


@router.get("/authorizations/{authorization_id}", response_model=HealthPlanAuthorizationInDB)
async def get_authorization(
    authorization_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get authorization by ID"""
    try:
        service = HealthPlanIntegrationService(db)
        authorization = service.db.query(service.db.query(HealthPlanAuthorization).filter(
            HealthPlanAuthorization.id == authorization_id
        ).first())
        if not authorization:
            raise HTTPException(status_code=404, detail="Authorization not found")
        return HealthPlanAuthorizationInDB.from_orm(authorization)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting authorization: {e}")
        raise HTTPException(status_code=500, detail="Error getting authorization")


# Eligibility Management
@router.post("/eligibility", response_model=HealthPlanEligibilityInDB)
async def create_eligibility_check(
    eligibility_data: HealthPlanEligibilityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create a new eligibility check"""
    try:
        service = HealthPlanIntegrationService(db)
        return service.create_eligibility_check(eligibility_data)
    except Exception as e:
        logger.error(f"Error creating eligibility check: {e}")
        raise HTTPException(status_code=500, detail="Error creating eligibility check")


@router.get("/eligibility", response_model=List[HealthPlanEligibilityInDB])
async def get_eligibility_checks(
    provider_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    is_eligible: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get eligibility checks with search filters"""
    try:
        search_params = HealthPlanEligibilitySearch(
            provider_id=provider_id,
            patient_id=patient_id,
            is_eligible=is_eligible,
            date_from=date_from,
            date_to=date_to
        )
        
        service = HealthPlanIntegrationService(db)
        return service.get_eligibility_checks(search_params, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting eligibility checks: {e}")
        raise HTTPException(status_code=500, detail="Error getting eligibility checks")


# Dashboard and Analytics
@router.get("/dashboard", response_model=HealthPlanDashboardData)
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get dashboard data for health plan integrations"""
    try:
        service = HealthPlanIntegrationService(db)
        return service.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Error getting dashboard data")


# Connection Logs
@router.get("/logs", response_model=List[HealthPlanConnectionLogInDB])
async def get_connection_logs(
    provider_id: Optional[int] = None,
    request_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get connection logs with filters"""
    try:
        query = db.query(HealthPlanConnectionLog)
        
        if provider_id:
            query = query.filter(HealthPlanConnectionLog.provider_id == provider_id)
        if request_type:
            query = query.filter(HealthPlanConnectionLog.request_type == request_type)
        if date_from:
            query = query.filter(HealthPlanConnectionLog.timestamp >= date_from)
        if date_to:
            query = query.filter(HealthPlanConnectionLog.timestamp <= date_to)
        
        logs = query.order_by(desc(HealthPlanConnectionLog.timestamp)).offset(skip).limit(limit).all()
        return [HealthPlanConnectionLogInDB.from_orm(log) for log in logs]
    except Exception as e:
        logger.error(f"Error getting connection logs: {e}")
        raise HTTPException(status_code=500, detail="Error getting connection logs")


# Configuration Management
@router.post("/configuration", response_model=HealthPlanConfigurationInDB)
async def create_configuration(
    config_data: HealthPlanConfigurationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Create health plan integration configuration"""
    try:
        config = HealthPlanConfiguration(**config_data.dict())
        db.add(config)
        db.commit()
        db.refresh(config)
        return HealthPlanConfigurationInDB.from_orm(config)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating configuration: {e}")
        raise HTTPException(status_code=500, detail="Error creating configuration")


@router.get("/configuration", response_model=List[HealthPlanConfigurationInDB])
async def get_configurations(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Get health plan integration configurations"""
    try:
        configs = db.query(HealthPlanConfiguration).all()
        return [HealthPlanConfigurationInDB.from_orm(config) for config in configs]
    except Exception as e:
        logger.error(f"Error getting configurations: {e}")
        raise HTTPException(status_code=500, detail="Error getting configurations")


@router.put("/configuration/{config_id}", response_model=HealthPlanConfigurationInDB)
async def update_configuration(
    config_id: int,
    config_data: HealthPlanConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Update health plan integration configuration"""
    try:
        config = db.query(HealthPlanConfiguration).filter(HealthPlanConfiguration.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        update_data = config_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return HealthPlanConfigurationInDB.from_orm(config)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")
