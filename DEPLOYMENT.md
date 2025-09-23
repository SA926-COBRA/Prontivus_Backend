# Prontivus Backend - Render.com Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Create Web Service on Render.com
- Go to [Render.com Dashboard](https://dashboard.render.com)
- Click "New +" → "Web Service"
- Connect your GitHub repository

### 2. Configure Build Settings
- **Build Command**: `pip install --upgrade pip && pip install --no-cache-dir --only-binary :all: -r requirements.txt`
- **Start Command**: `python main.py`
- **Python Version**: `3.11` (NOT 3.13 - compatibility issues)
- **Alternative**: Use the provided `build.sh` script

### 3. Set Environment Variables
Copy these to your Render.com service environment:

```bash
# Database Configuration
DATABASE_URL=postgresql://prontivus_rh0l_user:eKdELoiPkpuvqiuD84ao7yfkltPy7oev@dpg-d39ab7fdiees7387nihg-a.oregon-postgres.render.com/prontivus_rh0l
DATABASE_URL_ASYNC=postgresql+asyncpg://prontivus_rh0l_user:eKdELoiPkpuvqiuD84ao7yfkltPy7oev@dpg-d39ab7fdiees7387nihg-a.oregon-postgres.render.com/prontivus_rh0l

# PostgreSQL Settings
POSTGRES_HOST=dpg-d39ab7fdiees7387nihg-a.oregon-postgres.render.com
POSTGRES_PORT=5432
POSTGRES_DB=prontivus_rh0l
POSTGRES_USER=prontivus_rh0l_user
POSTGRES_PASSWORD=eKdELoiPkpuvqiuD84ao7yfkltPy7oev
POSTGRES_SSL_MODE=require

# Application Settings
USE_SQLITE=false
USE_DATABASE=true
ENVIRONMENT=production
DEBUG=false

# Security (CHANGE THIS!)
SECRET_KEY=your-production-secret-key-change-this-in-production

# CORS Settings
ALLOWED_ORIGINS=["https://prontivus-frontend.vercel.app"]
ALLOWED_HOSTS=["your-backend-domain.onrender.com"]

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

### 4. Deploy and Test
- Click "Create Web Service"
- Wait for deployment to complete
- Test your API:
  - Health check: `https://your-backend.onrender.com/health`
  - API docs: `https://your-backend.onrender.com/docs`

## 🔧 Troubleshooting

### If Build Fails:
1. Check Python version is 3.11
2. Ensure all environment variables are set
3. Check build logs for specific errors

### If Database Connection Fails:
1. Verify DATABASE_URL is correct
2. Check PostgreSQL service is running
3. Ensure SSL mode is set to "require"

### If CORS Issues:
1. Update ALLOWED_ORIGINS with your frontend URL
2. Check ALLOWED_HOSTS includes your backend domain

## 📁 Files Included:
- `main.py` - FastAPI application entry point
- `requirements.txt` - Python dependencies (updated for compatibility)
- `.env` - Environment configuration
- `render.yaml` - Render.com configuration
- `build.sh` - Build script (optional)

## ✅ What Happens on Deployment:
1. **Automatic Database Initialization**: Tables created automatically
2. **Health Check**: Server starts and responds to health checks
3. **API Documentation**: Available at `/docs` endpoint
4. **Database Connection**: Connected to Render.com PostgreSQL

Your backend is ready for deployment! 🎉
