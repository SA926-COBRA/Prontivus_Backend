"""
Language and translation API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database.database import get_db
from app.schemas.language import (
    Language, LanguageCreate, LanguageUpdate,
    TranslationKey, TranslationKeyCreate, TranslationKeyUpdate,
    Translation, TranslationCreate, TranslationUpdate,
    UserLanguagePreference, UserLanguagePreferenceCreate, UserLanguagePreferenceUpdate,
    LanguageTranslationResponse, BulkTranslationCreate, TranslationSearchRequest
)
from app.services.language_service import LanguageService
from app.api.v1.dependencies.auth import get_current_user_flexible

router = APIRouter()

# Language Management Endpoints
@router.get("/languages", response_model=List[Language])
async def get_languages(
    active_only: bool = Query(True, description="Only return active languages"),
    db: Session = Depends(get_db)
):
    """Get all supported languages"""
    service = LanguageService(db)
    return service.get_languages(active_only=active_only)

@router.get("/languages/{language_code}", response_model=Language)
async def get_language_by_code(
    language_code: str,
    db: Session = Depends(get_db)
):
    """Get language by code"""
    service = LanguageService(db)
    language = service.get_language_by_code(language_code)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found"
        )
    return language

@router.post("/languages", response_model=Language)
async def create_language(
    language_data: LanguageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Create a new language (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create languages"
        )
    
    service = LanguageService(db)
    return service.create_language(language_data)

@router.put("/languages/{language_id}", response_model=Language)
async def update_language(
    language_id: int,
    language_data: LanguageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Update a language (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update languages"
        )
    
    service = LanguageService(db)
    language = service.update_language(language_id, language_data)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    return language

# Translation Management Endpoints
@router.get("/translations/{language_code}", response_model=LanguageTranslationResponse)
async def get_translations_for_language(
    language_code: str,
    db: Session = Depends(get_db)
):
    """Get all translations for a specific language"""
    service = LanguageService(db)
    translations = service.get_translations_for_language(language_code)
    return LanguageTranslationResponse(
        language_code=language_code,
        translations=translations
    )

@router.get("/translations/{language_code}/{key}")
async def get_translation(
    language_code: str,
    key: str,
    fallback_code: str = Query("pt-BR", description="Fallback language code"),
    db: Session = Depends(get_db)
):
    """Get a specific translation"""
    service = LanguageService(db)
    translation = service.get_translation(key, language_code, fallback_code)
    return {"key": key, "value": translation, "language_code": language_code}

@router.post("/translations", response_model=Translation)
async def create_translation(
    translation_data: TranslationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Create a new translation (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create translations"
        )
    
    service = LanguageService(db)
    return service.create_translation(translation_data)

@router.put("/translations/{translation_id}", response_model=Translation)
async def update_translation(
    translation_id: int,
    translation_data: TranslationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Update a translation (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update translations"
        )
    
    service = LanguageService(db)
    translation = service.update_translation(translation_id, translation_data)
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found"
        )
    return translation

@router.post("/translations/bulk", response_model=List[Translation])
async def bulk_create_translations(
    bulk_data: BulkTranslationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Create multiple translations at once (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create bulk translations"
        )
    
    service = LanguageService(db)
    return service.bulk_create_translations(bulk_data)

# Translation Key Management Endpoints
@router.get("/translation-keys", response_model=List[TranslationKey])
async def get_translation_keys(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active keys"),
    db: Session = Depends(get_db)
):
    """Get all translation keys"""
    service = LanguageService(db)
    return service.get_translation_keys(category=category, active_only=active_only)

@router.post("/translation-keys", response_model=TranslationKey)
async def create_translation_key(
    key_data: TranslationKeyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Create a new translation key (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create translation keys"
        )
    
    service = LanguageService(db)
    return service.create_translation_key(key_data)

# User Language Preferences
@router.get("/user-preferences", response_model=Optional[UserLanguagePreference])
async def get_user_language_preference(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Get current user's language preference"""
    service = LanguageService(db)
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return service.get_user_language_preference(user_id)

@router.post("/user-preferences", response_model=UserLanguagePreference)
async def set_user_language_preference(
    language_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Set current user's language preference"""
    service = LanguageService(db)
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    try:
        return service.set_user_language_preference(user_id, language_code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Utility Endpoints
@router.post("/initialize")
async def initialize_language_system(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_flexible)
):
    """Initialize the language system with default data (Admin only)"""
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can initialize the language system"
        )
    
    service = LanguageService(db)
    service.initialize_default_languages()
    service.initialize_default_translations()
    
    return {"message": "Language system initialized successfully"}

@router.get("/health")
async def health_check():
    """Health check endpoint for language service"""
    return {
        "status": "healthy",
        "service": "language_service",
        "features": {
            "language_management": True,
            "translation_management": True,
            "user_preferences": True,
            "bulk_operations": True
        }
    }
