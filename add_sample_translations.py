#!/usr/bin/env python3
"""
Script to add sample translations
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.language_service import LanguageService
from app.schemas.language import TranslationCreate

def add_sample_translations():
    """Add sample translations"""
    try:
        # Connect to database
        engine = create_engine(settings.constructed_database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🌐 Adding sample translations...")
        print("=" * 50)
        
        # Initialize language service
        language_service = LanguageService(db)
        
        # Get languages
        pt_lang = language_service.get_language_by_code('pt-BR')
        en_lang = language_service.get_language_by_code('en-US')
        es_lang = language_service.get_language_by_code('es-ES')
        
        if not pt_lang or not en_lang or not es_lang:
            print("❌ Languages not found")
            return False
        
        # Sample translations
        translations = {
            'auth.login.title': {
                'pt-BR': 'Entrar',
                'en-US': 'Login',
                'es-ES': 'Iniciar Sesión'
            },
            'auth.login.email': {
                'pt-BR': 'Email',
                'en-US': 'Email',
                'es-ES': 'Correo'
            },
            'auth.login.password': {
                'pt-BR': 'Senha',
                'en-US': 'Password',
                'es-ES': 'Contraseña'
            },
            'auth.login.submit': {
                'pt-BR': 'Entrar',
                'en-US': 'Login',
                'es-ES': 'Iniciar Sesión'
            },
            'common.cancel': {
                'pt-BR': 'Cancelar',
                'en-US': 'Cancel',
                'es-ES': 'Cancelar'
            },
            'common.save': {
                'pt-BR': 'Salvar',
                'en-US': 'Save',
                'es-ES': 'Guardar'
            },
            'common.delete': {
                'pt-BR': 'Excluir',
                'en-US': 'Delete',
                'es-ES': 'Eliminar'
            },
            'common.edit': {
                'pt-BR': 'Editar',
                'en-US': 'Edit',
                'es-ES': 'Editar'
            },
            'dashboard.title': {
                'pt-BR': 'Painel de Controle',
                'en-US': 'Dashboard',
                'es-ES': 'Panel de Control'
            },
            'dashboard.welcome': {
                'pt-BR': 'Bem-vindo',
                'en-US': 'Welcome',
                'es-ES': 'Bienvenido'
            }
        }
        
        # Add translations
        for key_name, lang_translations in translations.items():
            # Get translation key
            translation_key = language_service.get_translation_key_by_key(key_name)
            if not translation_key:
                print(f"⚠️ Translation key '{key_name}' not found, skipping...")
                continue
            
            # Add translations for each language
            for lang_code, value in lang_translations.items():
                lang = language_service.get_language_by_code(lang_code)
                if not lang:
                    print(f"⚠️ Language '{lang_code}' not found, skipping...")
                    continue
                
                # Check if translation already exists
                existing_translation = db.execute(text("""
                    SELECT id FROM translations 
                    WHERE translation_key_id = :key_id AND language_id = :lang_id
                """), {"key_id": translation_key.id, "lang_id": lang.id}).fetchone()
                
                if existing_translation:
                    print(f"   Translation for '{key_name}' in '{lang_code}' already exists, skipping...")
                    continue
                
                # Create translation
                translation_data = TranslationCreate(
                    translation_key_id=translation_key.id,
                    language_id=lang.id,
                    value=value
                )
                language_service.create_translation(translation_data)
                print(f"   ✅ Added '{key_name}' -> '{value}' for {lang_code}")
        
        print("\n✅ Sample translations added successfully!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to add sample translations: {e}")
        return False

if __name__ == "__main__":
    success = add_sample_translations()
    sys.exit(0 if success else 1)
