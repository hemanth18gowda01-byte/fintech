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
    echo "   - "mongodb+srv://dbshama:#Dbshama*123@cluster0.4i8kgsg.mongodb.net/?appName=Cluster0"
    echo "   - "56c867c8bc47815887438432f87e08461e582fd7a886d69854d6af5f7664b73c516fbf1c52ebd530dc6ed7aac5e6817c36672c57ab19f4360d1467df6f43fa10"
    echo "   - "Lv24oaXrGe2JacbPl-8Y_JkcFFoH2ks7TQg8JaO4Wcs="
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
