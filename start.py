#!/usr/bin/env python3
"""
Render deployment startup script
"""

import os
import sys
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('DEBUG', 'False')

print("🚀 Starting Prontivus Backend for Render deployment")
print(f"📡 Working directory: {os.getcwd()}")
print(f"🌐 Environment: {os.getenv('ENVIRONMENT')}")
print(f"🔧 Debug: {os.getenv('DEBUG')}")
print(f"📊 Port: {os.getenv('PORT', '8000')}")

try:
    # Import the main app
    from main import app
    print("✅ Main app imported successfully")
    
    # Start server
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        reload=False
    )
    
except Exception as e:
    print(f"❌ Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
