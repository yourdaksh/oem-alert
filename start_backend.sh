#!/bin/bash
# Script to easily install dependencies and start the FastAPI Backend

echo "🚀 Setting up the OEM Alert Backend..."

# The system Python environment that we created earlier
VENV_PYTHON="venv_new/bin/python"
VENV_PIP="venv_new/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment 'venv_new' not found in $PWD."
    echo "Please run this script from the 'oem-alert' directory."
    exit 1
fi

echo "📦 Installing backend dependencies..."
$VENV_PIP install -r backend/requirements.txt

echo "✅ Dependencies installed!"
echo "🌐 Starting FastAPI Server on port 8000..."

# Start the uvicorn server via our main.py
$VENV_PYTHON -m backend.main
