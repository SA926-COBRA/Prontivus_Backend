"""
User endpoints - Database connected
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.services.security_monitor import get_security_monitor

router = APIRouter()

def get_current_user_from_token(request: Request, db: Session):
    """Get current user from JWT token"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify token and get user info
        auth_service = AuthService(db)
        token_data = auth_service.verify_token(token)
        
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/")
async def get_all_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """
    Get all users with filtering and pagination
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    - search: Search term for name or email
    - role: Filter by role (admin, doctor, secretary, patient)
    - is_active: Filter by active status
    """
    try:
        # Authenticate user
        current_user = get_current_user_from_token(request, db)
        
        # Build query
        query = """
            SELECT 
                u.id,
                u.email,
                u.username,
                u.full_name,
                u.cpf,
                u.phone,
                u.is_active,
                u.is_verified,
                u.is_superuser,
                u.crm,
                u.specialty,
                u.two_factor_enabled,
                u.failed_login_attempts,
                u.created_at,
                u.last_login,
                t.name as tenant_name
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE 1=1
        """
        
        params = {}
        
        # Add search filter
        if search:
            query += " AND (u.full_name ILIKE :search OR u.email ILIKE :search)"
            params["search"] = f"%{search}%"
        
        # Add role filter
        if role:
            if role == "admin":
                query += " AND u.is_superuser = true"
            elif role == "doctor":
                query += " AND u.crm IS NOT NULL"
            elif role == "secretary":
                query += " AND u.email ILIKE '%secretary%'"
            elif role == "patient":
                query += " AND u.cpf IS NOT NULL AND u.crm IS NULL"
        
        # Add active status filter
        if is_active is not None:
            query += " AND u.is_active = :is_active"
            params["is_active"] = is_active
        
        # Add pagination
        query += " ORDER BY u.created_at DESC LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Execute query
        cursor = db.execute(text(query), params)
        users = cursor.fetchall()
        
        # Convert to list of dictionaries
        users_list = []
        for user in users:
            # Determine role based on user data
            user_role = "patient"
            if user.is_superuser:
                user_role = "admin"
            elif user.crm:
                user_role = "doctor"
            elif "secretary" in user.email.lower():
                user_role = "secretary"
            
            user_dict = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "cpf": user.cpf,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "crm": user.crm,
                "specialty": user.specialty,
                "role": user_role,
                "two_factor_enabled": user.two_factor_enabled,
                "failed_login_attempts": user.failed_login_attempts,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "tenant_name": user.tenant_name
            }
            users_list.append(user_dict)
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM users u
            WHERE 1=1
        """
        
        count_params = {}
        if search:
            count_query += " AND (u.full_name ILIKE :search OR u.email ILIKE :search)"
            count_params["search"] = f"%{search}%"
        
        if role:
            if role == "admin":
                count_query += " AND u.is_superuser = true"
            elif role == "doctor":
                count_query += " AND u.crm IS NOT NULL"
            elif role == "secretary":
                count_query += " AND u.email ILIKE '%secretary%'"
            elif role == "patient":
                count_query += " AND u.cpf IS NOT NULL AND u.crm IS NULL"
        
        if is_active is not None:
            count_query += " AND u.is_active = :is_active"
            count_params["is_active"] = is_active
        
        count_cursor = db.execute(text(count_query), count_params)
        total_count = count_cursor.fetchone()[0]
        
        # Log audit event
        audit_service = AuditService(db)
        audit_service.log_data_access(
            user_id=current_user.user_id,
            entity_type="users",
            entity_id="all",
            action="list",
            ip_address=request.client.host if request.client else None,
            tenant_id=current_user.tenant_id,
            details={
                "filters": {
                    "search": search,
                    "role": role,
                    "is_active": is_active,
                    "skip": skip,
                    "limit": limit
                },
                "total_count": total_count
            }
        )
        
        return {
            "users": users_list,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_by_id(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    try:
        # Authenticate user
        current_user = get_current_user_from_token(request, db)
        
        # Get user from database
        query = """
            SELECT 
                u.id,
                u.email,
                u.username,
                u.full_name,
                u.cpf,
                u.phone,
                u.is_active,
                u.is_verified,
                u.is_superuser,
                u.crm,
                u.specialty,
                u.avatar_url,
                u.two_factor_enabled,
                u.failed_login_attempts,
                u.created_at,
                u.last_login,
                u.updated_at,
                t.name as tenant_name
            FROM users u
            LEFT JOIN tenants t ON u.tenant_id = t.id
            WHERE u.id = :user_id
        """
        
        cursor = db.execute(text(query), {"user_id": user_id})
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Determine role
        user_role = "patient"
        if user.is_superuser:
            user_role = "admin"
        elif user.crm:
            user_role = "doctor"
        elif "secretary" in user.email.lower():
            user_role = "secretary"
        
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "cpf": user.cpf,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "crm": user.crm,
            "specialty": user.specialty,
            "avatar_url": user.avatar_url,
            "role": user_role,
            "two_factor_enabled": user.two_factor_enabled,
            "failed_login_attempts": user.failed_login_attempts,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "tenant_name": user.tenant_name
        }
        
        # Log audit event
        audit_service = AuditService(db)
        audit_service.log_data_access(
            user_id=current_user.user_id,
            entity_type="users",
            entity_id=str(user_id),
            action="view",
            ip_address=request.client.host if request.client else None,
            tenant_id=current_user.tenant_id
        )
        
        return user_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.get("/stats/summary")
async def get_users_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get users statistics summary"""
    try:
        # Authenticate user
        current_user = get_current_user_from_token(request, db)
        
        # Get user statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_users,
                COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_users,
                COUNT(CASE WHEN is_superuser = true THEN 1 END) as admin_users,
                COUNT(CASE WHEN crm IS NOT NULL THEN 1 END) as doctor_users,
                COUNT(CASE WHEN cpf IS NOT NULL AND crm IS NULL THEN 1 END) as patient_users,
                COUNT(CASE WHEN email ILIKE '%secretary%' THEN 1 END) as secretary_users,
                COUNT(CASE WHEN two_factor_enabled = true THEN 1 END) as users_with_2fa,
                COUNT(CASE WHEN failed_login_attempts > 0 THEN 1 END) as users_with_failed_attempts
            FROM users
        """
        
        cursor = db.execute(text(stats_query))
        stats = cursor.fetchone()
        
        summary = {
            "total_users": stats.total_users,
            "active_users": stats.active_users,
            "inactive_users": stats.inactive_users,
            "admin_users": stats.admin_users,
            "doctor_users": stats.doctor_users,
            "patient_users": stats.patient_users,
            "secretary_users": stats.secretary_users,
            "users_with_2fa": stats.users_with_2fa,
            "users_with_failed_attempts": stats.users_with_failed_attempts,
            "generated_at": datetime.now().isoformat()
        }
        
        # Log audit event
        audit_service = AuditService(db)
        audit_service.log_data_access(
            user_id=current_user.user_id,
            entity_type="users",
            entity_id="stats",
            action="view_summary",
            ip_address=request.client.host if request.client else None,
            tenant_id=current_user.tenant_id
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user statistics: {str(e)}"
        )
