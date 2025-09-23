#!/bin/bash
# Render.com build script for Prontivus Backend

echo "🚀 Starting Prontivus Backend build on Render.com..."

# Set Python version
export PYTHON_VERSION=3.11

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install system dependencies if needed
echo "🔧 Installing system dependencies..."
apt-get update && apt-get install -y build-essential || echo "System dependencies already available"

# Install Python dependencies with pre-compiled wheels only
echo "📦 Installing Python dependencies (pre-compiled wheels only)..."
pip install --no-cache-dir --only-binary :all: -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads
mkdir -p logs

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 uploads
chmod 755 logs

echo "✅ Build completed successfully!"
echo "🎯 Ready to start Prontivus Backend server..."