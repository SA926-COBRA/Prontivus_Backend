"""
Language and translation service
"""

import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from app.models.language import Language, TranslationKey, Translation, UserLanguagePreference
from app.schemas.language import (
    LanguageCreate, LanguageUpdate, TranslationKeyCreate, TranslationKeyUpdate,
    TranslationCreate, TranslationUpdate, UserLanguagePreferenceCreate,
    LanguageTranslationResponse, BulkTranslationCreate, TranslationSearchRequest
)

logger = logging.getLogger(__name__)

class LanguageService:
    """Service for managing languages and translations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Language Management
    def get_languages(self, active_only: bool = True) -> List[Language]:
        """Get all languages"""
        query = self.db.query(Language)
        if active_only:
            query = query.filter(Language.is_active == True)
        return query.order_by(Language.sort_order, Language.name).all()
    
    def get_language_by_code(self, code: str) -> Optional[Language]:
        """Get language by code"""
        return self.db.query(Language).filter(
            and_(Language.code == code, Language.is_active == True)
        ).first()
    
    def get_default_language(self) -> Optional[Language]:
        """Get default language"""
        return self.db.query(Language).filter(
            and_(Language.is_default == True, Language.is_active == True)
        ).first()
    
    def create_language(self, language_data: LanguageCreate) -> Language:
        """Create a new language"""
        # If this is set as default, unset other defaults
        if language_data.is_default:
            self.db.query(Language).update({"is_default": False})
        
        language = Language(**language_data.model_dump())
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)
        return language
    
    def update_language(self, language_id: int, language_data: LanguageUpdate) -> Optional[Language]:
        """Update a language"""
        language = self.db.query(Language).filter(Language.id == language_id).first()
        if not language:
            return None
        
        # If this is set as default, unset other defaults
        if language_data.is_default:
            self.db.query(Language).update({"is_default": False})
        
        update_data = language_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(language, field, value)
        
        self.db.commit()
        self.db.refresh(language)
        return language
    
    # Translation Key Management
    def get_translation_keys(self, category: Optional[str] = None, active_only: bool = True) -> List[TranslationKey]:
        """Get translation keys"""
        query = self.db.query(TranslationKey)
        if active_only:
            query = query.filter(TranslationKey.is_active == True)
        if category:
            query = query.filter(TranslationKey.category == category)
        return query.order_by(TranslationKey.key).all()
    
    def get_translation_key_by_key(self, key: str) -> Optional[TranslationKey]:
        """Get translation key by key string"""
        return self.db.query(TranslationKey).filter(TranslationKey.key == key).first()
    
    def create_translation_key(self, key_data: TranslationKeyCreate) -> TranslationKey:
        """Create a new translation key"""
        translation_key = TranslationKey(**key_data.model_dump())
        self.db.add(translation_key)
        self.db.commit()
        self.db.refresh(translation_key)
        return translation_key
    
    # Translation Management
    def get_translations_for_language(self, language_code: str) -> Dict[str, str]:
        """Get all translations for a specific language"""
        query = text("""
            SELECT tk.key, t.value
            FROM translation_keys tk
            JOIN translations t ON tk.id = t.translation_key_id
            JOIN languages l ON t.language_id = l.id
            WHERE l.code = :language_code 
            AND tk.is_active = true 
            AND t.is_active = true
            ORDER BY tk.key
        """)
        
        result = self.db.execute(query, {"language_code": language_code}).fetchall()
        return {row[0]: row[1] for row in result}
    
    def get_translation(self, key: str, language_code: str, fallback_code: str = "pt-BR") -> Optional[str]:
        """Get a specific translation"""
        # Try to get translation in requested language
        query = text("""
            SELECT t.value
            FROM translations t
            JOIN translation_keys tk ON t.translation_key_id = tk.id
            JOIN languages l ON t.language_id = l.id
            WHERE tk.key = :key AND l.code = :language_code
            AND tk.is_active = true AND t.is_active = true
        """)
        
        result = self.db.execute(query, {"key": key, "language_code": language_code}).fetchone()
        if result:
            return result[0]
        
        # Fallback to default language
        if language_code != fallback_code:
            result = self.db.execute(query, {"key": key, "language_code": fallback_code}).fetchone()
            if result:
                return result[0]
        
        # Return the key itself as last resort
        return key
    
    def create_translation(self, translation_data: TranslationCreate) -> Translation:
        """Create a new translation"""
        translation = Translation(**translation_data.model_dump())
        self.db.add(translation)
        self.db.commit()
        self.db.refresh(translation)
        return translation
    
    def update_translation(self, translation_id: int, translation_data: TranslationUpdate) -> Optional[Translation]:
        """Update a translation"""
        translation = self.db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            return None
        
        update_data = translation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(translation, field, value)
        
        self.db.commit()
        self.db.refresh(translation)
        return translation
    
    def bulk_create_translations(self, bulk_data: BulkTranslationCreate) -> List[Translation]:
        """Create multiple translations at once"""
        translations = []
        for trans_data in bulk_data.translations:
            translation = Translation(**trans_data)
            self.db.add(translation)
            translations.append(translation)
        
        self.db.commit()
        for translation in translations:
            self.db.refresh(translation)
        
        return translations
    
    # User Language Preferences
    def get_user_language_preference(self, user_id: int) -> Optional[UserLanguagePreference]:
        """Get user's language preference"""
        return self.db.query(UserLanguagePreference).filter(
            and_(UserLanguagePreference.user_id == user_id, UserLanguagePreference.is_primary == True)
        ).first()
    
    def set_user_language_preference(self, user_id: int, language_code: str) -> UserLanguagePreference:
        """Set user's language preference"""
        # Get language by code
        language = self.get_language_by_code(language_code)
        if not language:
            raise ValueError(f"Language {language_code} not found")
        
        # Remove existing primary preference
        self.db.query(UserLanguagePreference).filter(
            and_(UserLanguagePreference.user_id == user_id, UserLanguagePreference.is_primary == True)
        ).update({"is_primary": False})
        
        # Create new preference
        preference = UserLanguagePreference(
            user_id=user_id,
            language_id=language.id,
            is_primary=True
        )
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference
    
    # Utility Methods
    def initialize_default_languages(self):
        """Initialize default languages"""
        default_languages = [
            {
                "code": "pt-BR",
                "name": "Portuguese (Brazil)",
                "native_name": "Português (Brasil)",
                "is_active": True,
                "is_default": True,
                "sort_order": 1
            },
            {
                "code": "en-US",
                "name": "English (US)",
                "native_name": "English (US)",
                "is_active": True,
                "is_default": False,
                "sort_order": 2
            },
            {
                "code": "es-ES",
                "name": "Spanish (Spain)",
                "native_name": "Español (España)",
                "is_active": True,
                "is_default": False,
                "sort_order": 3
            }
        ]
        
        for lang_data in default_languages:
            existing = self.get_language_by_code(lang_data["code"])
            if not existing:
                self.create_language(LanguageCreate(**lang_data))
                logger.info(f"Created default language: {lang_data['code']}")
    
    def initialize_default_translations(self):
        """Initialize default translations"""
        # This would typically load from JSON files or database seeds
        # For now, we'll create some basic translation keys
        default_keys = [
            {"key": "auth.login.title", "category": "auth", "description": "Login page title"},
            {"key": "auth.login.email", "category": "auth", "description": "Email field label"},
            {"key": "auth.login.password", "category": "auth", "description": "Password field label"},
            {"key": "auth.login.submit", "category": "auth", "description": "Login button text"},
            {"key": "dashboard.title", "category": "dashboard", "description": "Dashboard page title"},
            {"key": "dashboard.welcome", "category": "dashboard", "description": "Welcome message"},
            {"key": "common.save", "category": "common", "description": "Save button text"},
            {"key": "common.cancel", "category": "common", "description": "Cancel button text"},
            {"key": "common.delete", "category": "common", "description": "Delete button text"},
            {"key": "common.edit", "category": "common", "description": "Edit button text"},
        ]
        
        for key_data in default_keys:
            existing = self.get_translation_key_by_key(key_data["key"])
            if not existing:
                self.create_translation_key(TranslationKeyCreate(**key_data))
                logger.info(f"Created translation key: {key_data['key']}")
