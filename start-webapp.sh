#!/bin/bash

# Job Matching AI Platform - Startup Script

echo "🚀 Starting Job Matching AI Platform..."
echo ""

# Check if we're in the root directory
if [ ! -d "webapp" ]; then
    echo "❌ Error: webapp directory not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "Please install Python 3.9 or higher."
    exit 1
fi

echo "📦 Checking dependencies..."

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    cd webapp
    pip install -r requirements.txt --user
    cd ..
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🌐 Starting web server..."
echo "   Navigate to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd webapp
python3 app.py
