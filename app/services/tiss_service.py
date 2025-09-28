"""
TISS Integration Service
Service layer for TISS (Troca de Informação em Saúde Suplementar) integration
"""

import json
import requests
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from cryptography.fernet import Fernet
import base64
import os

from app.models.tiss import (
    TISSInsuranceOperator, TISSCredentials, TISSDoctorCode, 
    TISSTransaction, TISSConfiguration
)
from app.schemas.tiss import (
    TISSCredentialsCreate, TISSCredentialsUpdate, TISSCredentialsTestResponse,
    TISSDoctorCodeCreate, TISSDoctorCodeUpdate,
    TISSTransactionCreate, TISSTransactionUpdate,
    TISSConfigurationCreate, TISSConfigurationUpdate,
    TISSDashboardResponse, TISSOperatorStatus, TISSOperatorsStatusResponse
)

logger = logging.getLogger(__name__)


class TISSCryptoService:
    """Service for encrypting/decrypting TISS credentials"""
    
    def __init__(self):
        # In production, this should come from environment variables
        self.key = os.getenv('TISS_ENCRYPTION_KEY', Fernet.generate_key())
        if isinstance(self.key, str):
            self.key = self.key.encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt TISS data: {e}")
            return ""


class TISSService:
    """Main service for TISS integration operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crypto = TISSCryptoService()
    
    # Insurance Operators Management
    def create_insurance_operator(self, operator_data: dict) -> TISSInsuranceOperator:
        """Create a new insurance operator"""
        try:
            operator = TISSInsuranceOperator(**operator_data)
            self.db.add(operator)
            self.db.commit()
            self.db.refresh(operator)
            logger.info(f"Created TISS insurance operator: {operator.name}")
            return operator
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create insurance operator: {e}")
            raise
    
    def get_insurance_operators(self, active_only: bool = True) -> List[TISSInsuranceOperator]:
        """Get all insurance operators"""
        query = self.db.query(TISSInsuranceOperator)
        if active_only:
            query = query.filter(TISSInsuranceOperator.is_active == True)
        return query.order_by(TISSInsuranceOperator.name).all()
    
    def get_insurance_operator(self, operator_id: int) -> Optional[TISSInsuranceOperator]:
        """Get insurance operator by ID"""
        return self.db.query(TISSInsuranceOperator).filter(
            TISSInsuranceOperator.id == operator_id
        ).first()
    
    def update_insurance_operator(self, operator_id: int, update_data: dict) -> Optional[TISSInsuranceOperator]:
        """Update insurance operator"""
        try:
            operator = self.get_insurance_operator(operator_id)
            if not operator:
                return None
            
            for field, value in update_data.items():
                if hasattr(operator, field) and value is not None:
                    setattr(operator, field, value)
            
            self.db.commit()
            self.db.refresh(operator)
            logger.info(f"Updated TISS insurance operator: {operator.name}")
            return operator
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update insurance operator: {e}")
            raise
    
    # Credentials Management
    def create_credentials(self, tenant_id: int, credentials_data: TISSCredentialsCreate) -> TISSCredentials:
        """Create TISS credentials for a tenant"""
        try:
            # Encrypt sensitive data
            encrypted_data = credentials_data.dict()
            encrypted_data['password'] = self.crypto.encrypt(credentials_data.password)
            if credentials_data.token:
                encrypted_data['token'] = self.crypto.encrypt(credentials_data.token)
            
            encrypted_data['tenant_id'] = tenant_id
            
            credentials = TISSCredentials(**encrypted_data)
            self.db.add(credentials)
            self.db.commit()
            self.db.refresh(credentials)
            logger.info(f"Created TISS credentials for tenant {tenant_id}")
            return credentials
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create TISS credentials: {e}")
            raise
    
    def get_credentials(self, tenant_id: int, operator_id: Optional[int] = None) -> List[TISSCredentials]:
        """Get TISS credentials for a tenant"""
        query = self.db.query(TISSCredentials).filter(TISSCredentials.tenant_id == tenant_id)
        if operator_id:
            query = query.filter(TISSCredentials.operator_id == operator_id)
        return query.all()
    
    def get_credentials_by_id(self, credentials_id: int) -> Optional[TISSCredentials]:
        """Get TISS credentials by ID"""
        return self.db.query(TISSCredentials).filter(
            TISSCredentials.id == credentials_id
        ).first()
    
    def update_credentials(self, credentials_id: int, update_data: TISSCredentialsUpdate) -> Optional[TISSCredentials]:
        """Update TISS credentials"""
        try:
            credentials = self.get_credentials_by_id(credentials_id)
            if not credentials:
                return None
            
            update_dict = update_data.dict(exclude_unset=True)
            
            # Encrypt sensitive data if provided
            if 'password' in update_dict and update_dict['password']:
                update_dict['password'] = self.crypto.encrypt(update_dict['password'])
            if 'token' in update_dict and update_dict['token']:
                update_dict['token'] = self.crypto.encrypt(update_dict['token'])
            
            for field, value in update_dict.items():
                if hasattr(credentials, field) and value is not None:
                    setattr(credentials, field, value)
            
            self.db.commit()
            self.db.refresh(credentials)
            logger.info(f"Updated TISS credentials {credentials_id}")
            return credentials
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update TISS credentials: {e}")
            raise
    
    def test_credentials(self, credentials_id: int) -> TISSCredentialsTestResponse:
        """Test TISS credentials connection"""
        try:
            credentials = self.get_credentials_by_id(credentials_id)
            if not credentials:
                return TISSCredentialsTestResponse(
                    success=False,
                    message="Credentials not found"
                )
            
            # Decrypt credentials for testing
            decrypted_password = self.crypto.decrypt(credentials.password)
            decrypted_token = self.crypto.decrypt(credentials.token) if credentials.token else None
            
            # Determine URL based on environment
            url = credentials.homologation_url if credentials.environment == "homologation" else credentials.production_url
            
            if not url:
                return TISSCredentialsTestResponse(
                    success=False,
                    message="No URL configured for this environment"
                )
            
            # Test connection
            start_time = datetime.now()
            
            # This is a simplified test - in production, you'd implement actual TISS API calls
            test_payload = {
                "username": credentials.username,
                "password": decrypted_password,
                "token": decrypted_token
            }
            
            # Mock test - replace with actual TISS API call
            response = requests.post(
                f"{url}/test-connection",
                json=test_payload,
                timeout=30
            )
            
            connection_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                # Update credentials with success status
                credentials.connection_status = "success"
                credentials.last_connection_success = datetime.now()
                credentials.last_connection_error = None
                self.db.commit()
                
                return TISSCredentialsTestResponse(
                    success=True,
                    message="Connection successful",
                    connection_time=connection_time,
                    response_data=response.json() if response.content else None
                )
            else:
                # Update credentials with error status
                error_message = f"HTTP {response.status_code}: {response.text}"
                credentials.connection_status = "error"
                credentials.last_connection_error = error_message
                self.db.commit()
                
                return TISSCredentialsTestResponse(
                    success=False,
                    message=error_message,
                    connection_time=connection_time
                )
                
        except requests.exceptions.RequestException as e:
            # Update credentials with error status
            credentials.connection_status = "error"
            credentials.last_connection_error = str(e)
            self.db.commit()
            
            return TISSCredentialsTestResponse(
                success=False,
                message=f"Connection failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to test TISS credentials: {e}")
            return TISSCredentialsTestResponse(
                success=False,
                message=f"Test failed: {str(e)}"
            )
    
    # Doctor Codes Management
    def create_doctor_code(self, doctor_code_data: TISSDoctorCodeCreate) -> TISSDoctorCode:
        """Create doctor code for an operator"""
        try:
            doctor_code = TISSDoctorCode(**doctor_code_data.dict())
            self.db.add(doctor_code)
            self.db.commit()
            self.db.refresh(doctor_code)
            logger.info(f"Created TISS doctor code for doctor {doctor_code_data.doctor_id}")
            return doctor_code
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create TISS doctor code: {e}")
            raise
    
    def get_doctor_codes(self, doctor_id: Optional[int] = None, operator_id: Optional[int] = None) -> List[TISSDoctorCode]:
        """Get doctor codes"""
        query = self.db.query(TISSDoctorCode)
        if doctor_id:
            query = query.filter(TISSDoctorCode.doctor_id == doctor_id)
        if operator_id:
            query = query.filter(TISSDoctorCode.operator_id == operator_id)
        return query.filter(TISSDoctorCode.is_active == True).all()
    
    def update_doctor_code(self, doctor_code_id: int, update_data: TISSDoctorCodeUpdate) -> Optional[TISSDoctorCode]:
        """Update doctor code"""
        try:
            doctor_code = self.db.query(TISSDoctorCode).filter(
                TISSDoctorCode.id == doctor_code_id
            ).first()
            if not doctor_code:
                return None
            
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(doctor_code, field) and value is not None:
                    setattr(doctor_code, field, value)
            
            self.db.commit()
            self.db.refresh(doctor_code)
            logger.info(f"Updated TISS doctor code {doctor_code_id}")
            return doctor_code
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update TISS doctor code: {e}")
            raise
    
    # Configuration Management
    def get_configuration(self, tenant_id: int) -> Optional[TISSConfiguration]:
        """Get TISS configuration for a tenant"""
        return self.db.query(TISSConfiguration).filter(
            TISSConfiguration.tenant_id == tenant_id
        ).first()
    
    def create_or_update_configuration(self, tenant_id: int, config_data: TISSConfigurationCreate) -> TISSConfiguration:
        """Create or update TISS configuration"""
        try:
            existing_config = self.get_configuration(tenant_id)
            
            if existing_config:
                # Update existing configuration
                update_dict = config_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    if hasattr(existing_config, field) and value is not None:
                        setattr(existing_config, field, value)
                self.db.commit()
                self.db.refresh(existing_config)
                return existing_config
            else:
                # Create new configuration
                config_dict = config_data.dict()
                config_dict['tenant_id'] = tenant_id
                configuration = TISSConfiguration(**config_dict)
                self.db.add(configuration)
                self.db.commit()
                self.db.refresh(configuration)
                return configuration
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update TISS configuration: {e}")
            raise
    
    # Dashboard and Status
    def get_dashboard_data(self, tenant_id: int) -> TISSDashboardResponse:
        """Get TISS dashboard data"""
        try:
            # Get counts
            total_operators = self.db.query(TISSInsuranceOperator).count()
            active_operators = self.db.query(TISSInsuranceOperator).filter(
                TISSInsuranceOperator.is_active == True
            ).count()
            
            total_credentials = self.db.query(TISSCredentials).filter(
                TISSCredentials.tenant_id == tenant_id
            ).count()
            active_credentials = self.db.query(TISSCredentials).filter(
                and_(
                    TISSCredentials.tenant_id == tenant_id,
                    TISSCredentials.is_active == True
                )
            ).count()
            
            # Recent transactions (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            recent_transactions = self.db.query(TISSTransaction).filter(
                and_(
                    TISSTransaction.tenant_id == tenant_id,
                    TISSTransaction.created_at >= recent_date
                )
            ).count()
            
            # Success rate calculation
            total_transactions = self.db.query(TISSTransaction).filter(
                TISSTransaction.tenant_id == tenant_id
            ).count()
            successful_transactions = self.db.query(TISSTransaction).filter(
                and_(
                    TISSTransaction.tenant_id == tenant_id,
                    TISSTransaction.status == "success"
                )
            ).count()
            
            success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
            
            # Last connection status
            last_credentials = self.db.query(TISSCredentials).filter(
                TISSCredentials.tenant_id == tenant_id
            ).order_by(TISSCredentials.last_connection_success.desc()).first()
            
            last_connection_status = {
                "status": last_credentials.connection_status if last_credentials else "unknown",
                "last_success": last_credentials.last_connection_success if last_credentials else None,
                "last_error": last_credentials.last_connection_error if last_credentials else None
            }
            
            return TISSDashboardResponse(
                total_operators=total_operators,
                active_operators=active_operators,
                total_credentials=total_credentials,
                active_credentials=active_credentials,
                recent_transactions=recent_transactions,
                success_rate=round(success_rate, 2),
                last_connection_status=last_connection_status
            )
        except Exception as e:
            logger.error(f"Failed to get TISS dashboard data: {e}")
            raise
    
    def get_operators_status(self, tenant_id: int) -> TISSOperatorsStatusResponse:
        """Get status of all TISS operators for a tenant"""
        try:
            credentials = self.get_credentials(tenant_id)
            operators_status = []
            
            for cred in credentials:
                operator = self.get_insurance_operator(cred.operator_id)
                if operator:
                    operators_status.append(TISSOperatorStatus(
                        operator_id=operator.id,
                        operator_name=operator.name,
                        environment=cred.environment,
                        connection_status=cred.connection_status,
                        last_connection_success=cred.last_connection_success,
                        last_connection_error=cred.last_connection_error,
                        is_active=cred.is_active
                    ))
            
            active_operators = len([op for op in operators_status if op.is_active])
            error_operators = len([op for op in operators_status if op.connection_status == "error"])
            
            return TISSOperatorsStatusResponse(
                operators=operators_status,
                total_operators=len(operators_status),
                active_operators=active_operators,
                error_operators=error_operators
            )
        except Exception as e:
            logger.error(f"Failed to get operators status: {e}")
            raise
