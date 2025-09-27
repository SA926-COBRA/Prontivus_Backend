"""
Language and translation models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from ..utils.database_compat import (
    get_json_type, get_datetime_type, get_string_type, 
    get_boolean_type, get_integer_type, get_foreign_key
)

class Language(Base):
    """Supported languages"""
    __tablename__ = "languages"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    code = Column(get_string_type(10), unique=True, nullable=False, index=True)  # pt-BR, en-US, etc.
    name = Column(get_string_type(100), nullable=False)  # Portuguese (Brazil), English (US), etc.
    native_name = Column(get_string_type(100), nullable=False)  # Português (Brasil), English (US), etc.
    is_active = Column(get_boolean_type(), default=True)
    is_default = Column(get_boolean_type(), default=False)
    sort_order = Column(get_integer_type(), default=0)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    translations = relationship("Translation", back_populates="language")

class TranslationKey(Base):
    """Translation keys for the application"""
    __tablename__ = "translation_keys"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    key = Column(get_string_type(255), unique=True, nullable=False, index=True)  # e.g., "auth.login.title"
    category = Column(get_string_type(100), nullable=True)  # e.g., "auth", "dashboard", "forms"
    description = Column(Text, nullable=True)  # Description of what this key is for
    is_active = Column(get_boolean_type(), default=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    translations = relationship("Translation", back_populates="translation_key")

class Translation(Base):
    """Translation values for each language"""
    __tablename__ = "translations"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    translation_key_id = Column(get_integer_type(), get_foreign_key("translation_keys.id"), nullable=False)
    language_id = Column(get_integer_type(), get_foreign_key("languages.id"), nullable=False)
    value = Column(Text, nullable=False)  # The actual translated text
    is_active = Column(get_boolean_type(), default=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    translation_key = relationship("TranslationKey", back_populates="translations")
    language = relationship("Language", back_populates="translations")
    
    # Unique constraint
    __table_args__ = (
        {"extend_existing": True}
    )

class UserLanguagePreference(Base):
    """User language preferences"""
    __tablename__ = "user_language_preferences"
    
    id = Column(get_integer_type(), primary_key=True, index=True)
    user_id = Column(get_integer_type(), get_foreign_key("users.id"), nullable=False)
    language_id = Column(get_integer_type(), get_foreign_key("languages.id"), nullable=False)
    is_primary = Column(get_boolean_type(), default=True)  # Primary language for the user
    
    # Timestamps
    created_at = Column(get_datetime_type(), server_default=func.now())
    updated_at = Column(get_datetime_type(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    language = relationship("Language", foreign_keys=[language_id])
    
    # Unique constraint
    __table_args__ = (
        {"extend_existing": True}
    )
