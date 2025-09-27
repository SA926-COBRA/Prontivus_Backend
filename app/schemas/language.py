"""
Language and translation schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LanguageBase(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    code: str = Field(..., min_length=2, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    native_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    is_default: bool = False
    sort_order: int = Field(0, ge=0)

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    native_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class Language(LanguageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TranslationKeyBase(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    key: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: bool = True

class TranslationKeyCreate(TranslationKeyBase):
    pass

class TranslationKeyUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    key: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TranslationKey(TranslationKeyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TranslationBase(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    translation_key_id: int
    language_id: int
    value: str
    is_active: bool = True

class TranslationCreate(TranslationBase):
    pass

class TranslationUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    translation_key_id: Optional[int] = None
    language_id: Optional[int] = None
    value: Optional[str] = None
    is_active: Optional[bool] = None

class Translation(TranslationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TranslationWithDetails(Translation):
    translation_key: TranslationKey
    language: Language

class UserLanguagePreferenceBase(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    user_id: int
    language_id: int
    is_primary: bool = True

class UserLanguagePreferenceCreate(UserLanguagePreferenceBase):
    pass

class UserLanguagePreferenceUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    language_id: Optional[int] = None
    is_primary: Optional[bool] = None

class UserLanguagePreference(UserLanguagePreferenceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    language: Language

    class Config:
        from_attributes = True

class LanguageTranslationResponse(BaseModel):
    """Response model for language-specific translations"""
    language_code: str
    translations: Dict[str, str]  # key -> translated value

class BulkTranslationCreate(BaseModel):
    """Model for bulk translation creation"""
    translations: List[Dict[str, Any]] = Field(..., description="List of translation objects")

class TranslationSearchRequest(BaseModel):
    """Model for searching translations"""
    language_code: Optional[str] = None
    category: Optional[str] = None
    search_term: Optional[str] = None
    is_active: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
