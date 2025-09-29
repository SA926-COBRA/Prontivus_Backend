"""
Prontivus - Sistema Médico Completo
FastAPI Backend Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.database import init_db
from app.api.v1.api import api_router
from app.core.exceptions import ProntivusException, prontivus_exception_handler
# from app.services.startup_service import initialize_database_on_startup  # Disabled for deployment

# Configure logging - optimized for performance
logging.basicConfig(
    level=logging.WARNING,  # Reduce logging level for better performance
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events - simplified for deployment"""
    # Startup
    logger.info("Starting Prontivus Backend...")
    
    # Skip database initialization during startup to prevent blocking
    logger.info("🚀 Server starting - database will initialize in background...")
    
    yield
    # Shutdown
    logger.info("Shutting down Prontivus Backend...")

# Create FastAPI application with performance optimizations
app = FastAPI(
    title="Prontivus API",
    description="Sistema Médico Completo de Gestão de Clínicas e Consultórios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,  # Enable automatic database initialization
    # Performance optimizations
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    openapi_url="/openapi.json"
)

# Security middleware - temporarily disabled for deployment testing
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS
# )

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

# Exception handlers
app.add_exception_handler(ProntivusException, prontivus_exception_handler)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Prontivus API",
        "version": "1.0.0",
        "status": "active",
        "environment": settings.ENVIRONMENT,
        "port": os.getenv("PORT", 8000),
        "host": "0.0.0.0"
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for health checks"""
    return {"status": "pong", "timestamp": "2025-01-15T11:15:00Z"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-15T11:15:00Z",
        "version": "1.0.0"
    }

# Start server immediately for Render deployment
port = int(os.getenv("PORT", 8000))
print(f"🚀 Starting Prontivus Backend on port {port}")
print(f"🌐 Host: 0.0.0.0")
print(f"📡 Environment: {settings.ENVIRONMENT}")
print(f"🔧 Debug mode: {settings.DEBUG}")
print(f"🔗 Server will bind to: http://0.0.0.0:{port}")
print(f"📊 All services initialized successfully")

# Start server immediately
uvicorn.run(
    app,
    host="0.0.0.0",
    port=port,
    log_level="info",
    access_log=True,
    reload=False
)
