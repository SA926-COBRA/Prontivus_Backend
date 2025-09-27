#!/usr/bin/env python3
"""
Test script for multilingual support
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.language_service import LanguageService

def test_language_system():
    """Test the language system"""
    try:
        # Connect to database
        engine = create_engine(settings.constructed_database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🌐 Testing Language System...")
        print("=" * 50)
        
        # Initialize language service
        language_service = LanguageService(db)
        
        # Test 1: Get available languages
        print("1. Testing available languages...")
        languages = language_service.get_languages()
        print(f"   Found {len(languages)} languages:")
        for lang in languages:
            print(f"   - {lang.code}: {lang.name} ({lang.native_name})")
        
        # Test 2: Get translations for Portuguese
        print("\n2. Testing Portuguese translations...")
        pt_translations = language_service.get_translations_for_language('pt-BR')
        print(f"   Found {len(pt_translations)} Portuguese translations")
        if pt_translations:
            print("   Sample translations:")
            for i, (key, value) in enumerate(list(pt_translations.items())[:5]):
                print(f"   - {key}: {value}")
        
        # Test 3: Get translations for English
        print("\n3. Testing English translations...")
        en_translations = language_service.get_translations_for_language('en-US')
        print(f"   Found {len(en_translations)} English translations")
        if en_translations:
            print("   Sample translations:")
            for i, (key, value) in enumerate(list(en_translations.items())[:5]):
                print(f"   - {key}: {value}")
        
        # Test 4: Test specific translation
        print("\n4. Testing specific translation...")
        login_title_pt = language_service.get_translation('auth.login.title', 'pt-BR')
        login_title_en = language_service.get_translation('auth.login.title', 'en-US')
        print(f"   Portuguese: {login_title_pt}")
        print(f"   English: {login_title_en}")
        
        # Test 5: Test fallback
        print("\n5. Testing fallback...")
        fallback_test = language_service.get_translation('nonexistent.key', 'en-US', 'pt-BR')
        print(f"   Fallback test: {fallback_test}")
        
        print("\n✅ Language system test completed successfully!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Language system test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_language_system()
    sys.exit(0 if success else 1)
