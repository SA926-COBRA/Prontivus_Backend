"""
User lookup endpoint for login optimization
Checks user type before authentication to route to correct endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel

from app.database.database import get_db

router = APIRouter()

class UserLookupRequest(BaseModel):
    email_or_cpf: str

class UserLookupResponse(BaseModel):
    exists: bool
    user_type: Optional[str] = None  # "staff" or "patient"
    user_role: Optional[str] = None  # "admin", "doctor", "secretary", "patient"
    is_active: Optional[bool] = None
    requires_2fa: Optional[bool] = None

@router.post("/lookup", response_model=UserLookupResponse)
async def lookup_user_type(
    request_data: UserLookupRequest,
    db: Session = Depends(get_db)
):
    """
    Lookup user type and role before authentication
    This helps the frontend determine which authentication endpoint to use
    """
    try:
        email_or_cpf = request_data.email_or_cpf.strip()
        
        # Query to find user by email or CPF
        query = """
            SELECT 
                u.id,
                u.email,
                u.cpf,
                u.is_active,
                u.is_superuser,
                u.crm,
                u.two_factor_enabled,
                u.email as user_email
            FROM users u
            WHERE (u.email = :email_or_cpf OR u.cpf = :email_or_cpf)
            LIMIT 1
        """
        
        cursor = db.execute(text(query), {"email_or_cpf": email_or_cpf})
        user = cursor.fetchone()
        
        if not user:
            return UserLookupResponse(exists=False)
        
        # Determine user type and role based on actual role assignments
        # Query user roles from database
        role_query = """
            SELECT r.name 
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
        """
        
        role_cursor = db.execute(text(role_query), {"user_id": user.id})
        user_roles = [row[0] for row in role_cursor.fetchall()]
        
        if not user_roles:
            # User has no roles - treat as patient
            user_type = "patient"
            user_role = "patient"
        else:
            # User has roles - determine type and role
            primary_role = user_roles[0]  # Use first role as primary
            
            if primary_role == "patient":
                user_type = "patient"
                user_role = "patient"
            else:
                # Any other role (admin, doctor, secretary, etc.) is staff
                user_type = "staff"
                user_role = primary_role
        
        return UserLookupResponse(
            exists=True,
            user_type=user_type,
            user_role=user_role,
            is_active=user.is_active,
            requires_2fa=user.two_factor_enabled
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error looking up user: {str(e)}"
        )

@router.post("/check-credentials", response_model=dict)
async def check_user_credentials(
    request_data: UserLookupRequest,
    db: Session = Depends(get_db)
):
    """
    Check if user exists and is active (without revealing sensitive info)
    Used for login form validation
    """
    try:
        email_or_cpf = request_data.email_or_cpf.strip()
        
        # Query to check if user exists and is active
        query = """
            SELECT 
                u.is_active,
                u.failed_login_attempts,
                u.locked_until
            FROM users u
            WHERE (u.email = :email_or_cpf OR u.cpf = :email_or_cpf)
            LIMIT 1
        """
        
        cursor = db.execute(text(query), {"email_or_cpf": email_or_cpf})
        user = cursor.fetchone()
        
        if not user:
            return {
                "exists": False,
                "message": "Usuário não encontrado"
            }
        
        if not user.is_active:
            return {
                "exists": True,
                "active": False,
                "message": "Conta desativada"
            }
        
        if user.locked_until:
            from datetime import datetime
            if user.locked_until > datetime.utcnow():
                return {
                    "exists": True,
                    "active": True,
                    "locked": True,
                    "message": "Conta temporariamente bloqueada"
                }
        
        return {
            "exists": True,
            "active": True,
            "locked": False,
            "failed_attempts": user.failed_login_attempts
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking user credentials: {str(e)}"
        )
