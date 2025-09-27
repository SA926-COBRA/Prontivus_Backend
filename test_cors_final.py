#!/usr/bin/env python3
"""
Simple test to verify CORS fix after deployment
"""

import requests
import time

def test_cors_after_deployment():
    """Test CORS after deployment"""
    
    base_url = "https://prontivus-backend-pa1e.onrender.com"
    frontend_origin = "https://prontivus-frontend.vercel.app"
    
    print("🧪 Testing CORS After Deployment")
    print("=" * 50)
    
    # Wait a moment for deployment to complete
    print("⏳ Waiting for deployment to complete...")
    time.sleep(10)
    
    # Test translations endpoint with proper CORS headers
    print("\n1. Testing translations endpoint with CORS...")
    try:
        headers = {
            'Origin': frontend_origin,
            'Accept': 'application/json'
        }
        response = requests.get(f"{base_url}/api/v1/language/translations/pt-BR", headers=headers)
        print(f"   Status: {response.status_code}")
        
        # Check CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NOT_SET')
        print(f"   CORS Origin: {cors_origin}")
        
        if cors_origin == frontend_origin:
            print(f"   ✅ CORS is correctly configured!")
        elif cors_origin == '*':
            print(f"   ⚠️ CORS is set to wildcard (may cause issues)")
        else:
            print(f"   ❌ CORS origin mismatch!")
        
        if response.status_code == 200:
            data = response.json()
            translations = data.get('translations', {})
            print(f"   ✅ API working! Found {len(translations)} translations")
        else:
            print(f"   ❌ API error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test languages endpoint
    print("\n2. Testing languages endpoint...")
    try:
        headers = {'Origin': frontend_origin}
        response = requests.get(f"{base_url}/api/v1/language/languages", headers=headers)
        print(f"   Status: {response.status_code}")
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NOT_SET')
        print(f"   CORS Origin: {cors_origin}")
        
        if response.status_code == 200:
            languages = response.json()
            print(f"   ✅ API working! Found {len(languages)} languages")
        else:
            print(f"   ❌ API error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ CORS testing completed!")

if __name__ == "__main__":
    test_cors_after_deployment()
