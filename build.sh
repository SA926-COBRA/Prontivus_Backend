#!/bin/bash
# Render.com build script for Prontivus Backend

echo "🚀 Starting Prontivus Backend build on Render.com..."

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies with specific flags for Render.com
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir --upgrade -r requirements.txt

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
