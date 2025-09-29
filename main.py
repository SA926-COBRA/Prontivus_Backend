"""
Prontivus - Sistema Médico Completo
FastAPI Backend Application
"""

import os
import uvicorn
from fastapi import FastAPI

# Create FastAPI application
app = FastAPI(
    title="Prontivus API",
    description="Sistema Médico Completo de Gestão de Clínicas e Consultórios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Prontivus API",
        "version": "1.0.0",
        "status": "active",
        "port": os.getenv("PORT", 8000),
        "host": "0.0.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "port": os.getenv("PORT", 8000)
    }

# Start server immediately for Render deployment
port = int(os.getenv("PORT", 8000))
print(f"🚀 Starting Prontivus Backend on port {port}")
print(f"🌐 Host: 0.0.0.0")
print(f"🔗 Server will bind to: http://0.0.0.0:{port}")

uvicorn.run(
    app,
    host="0.0.0.0",
    port=port,
    log_level="info",
    access_log=True,
    reload=False
)
