# 🚨 Render.com Deployment Troubleshooting Guide

## Common Deployment Issues & Solutions

### 1. **Python Version Issues**
**Problem**: Using Python 3.13 (not fully supported)
**Solution**: 
- Set Python version to `3.11` in Render.com settings
- Add `runtime.txt` with `python-3.11.9`

### 2. **Package Version Conflicts**
**Problem**: Specific package versions not available
**Solution**: Use the minimal requirements file

### 3. **Build Command Issues**
**Problem**: Build command not working
**Solution**: Use this exact command:
```bash
pip install --upgrade pip && pip install --no-cache-dir --only-binary :all: -r requirements-minimal.txt
```

### 4. **Environment Variables Missing**
**Problem**: Database connection fails
**Solution**: Set these environment variables in Render.com:
```bash
DATABASE_URL=postgresql://prontivus_rh0l_user:eKdELoiPkpuvqiuD84ao7yfkltPy7oev@dpg-d39ab7fdiees7387nihg-a.oregon-postgres.render.com/prontivus_rh0l
USE_SQLITE=false
USE_DATABASE=true
ENVIRONMENT=production
SECRET_KEY=your-production-secret-key-change-this
ALLOWED_ORIGINS=["https://prontivus-frontend.vercel.app"]
```

## 🔧 **Quick Fix Steps:**

1. **Use Minimal Requirements**:
   - Change build command to use `requirements-minimal.txt`
   - This removes potentially problematic packages

2. **Set Python Version**:
   - In Render.com settings, set Python version to `3.11`
   - Or add `runtime.txt` file

3. **Check Environment Variables**:
   - Ensure all required environment variables are set
   - Check DATABASE_URL is correct

4. **Use Correct Build Command**:
   ```bash
   pip install --upgrade pip && pip install --no-cache-dir --only-binary :all: -r requirements-minimal.txt
   ```

## 📋 **Deployment Checklist:**

- [ ] Python version set to 3.11
- [ ] Build command uses `--only-binary :all:`
- [ ] All environment variables set
- [ ] Using minimal requirements file
- [ ] Start command: `python main.py`

**Please share the specific error message for more targeted help!**
