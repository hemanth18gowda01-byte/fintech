#!/bin/bash

# FinTrack Backend Deployment Script
# This script helps you deploy the backend quickly

echo "🚀 FinTrack Backend Deployment Helper"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your configuration:"
    echo "   - MONGO_URI (from MongoDB Atlas)"
    echo "   - JWT_SECRET_KEY (generate with: openssl rand -hex 32)"
    echo "   - FERNET_KEY (generate with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
    echo ""
    echo "Press Enter after you've updated .env..."
    read
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt
echo ""

# Test local run
echo "🧪 Testing local server..."
echo "Starting server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
