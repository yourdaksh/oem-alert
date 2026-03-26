#!/bin/bash

# Vulnerability Scrapper - Installation Script
echo "Installing Vulnerability Scrapper..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    echo "Please check your internet connection and try again."
    exit 1
fi

echo "✅ Dependencies installed successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'python3 setup_database.py setup' to initialize the database"
echo "2. Copy 'env.example' to '.env' and configure your email settings"
echo "3. Run 'python3 test_system.py' to test the installation"
echo "4. Run 'streamlit run app.py' to start the web interface"
echo "5. Run './setup.sh' to set up automated scanning"
echo ""
echo "For more information, see README.md"
