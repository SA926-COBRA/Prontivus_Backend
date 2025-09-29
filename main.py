"""
Prontivus - Sistema Médico Completo
FastAPI Backend Application
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router

# Create FastAPI application
app = FastAPI(
    title="Prontivus API",
    description="Sistema Médico Completo de Gestão de Clínicas e Consultórios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prontivus-frontend.vercel.app",
        "https://prontivus-frontend-git-main-prontivus.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

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
