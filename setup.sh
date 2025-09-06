#!/bin/bash

# OEM Vulnerability Alert Platform - Setup Script
# This script sets up the cron job for automated vulnerability scanning

echo "Setting up OEM Vulnerability Alert Platform..."

# Get the current directory
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if the required files exist
if [ ! -f "run_scrapers.py" ]; then
    echo "Error: run_scrapers.py not found in current directory"
    exit 1
fi

if [ ! -f "setup_database.py" ]; then
    echo "Error: setup_database.py not found in current directory"
    exit 1
fi

# Initialize database
echo "Initializing database..."
python3 setup_database.py setup

if [ $? -ne 0 ]; then
    echo "Error: Database initialization failed"
    exit 1
fi

# Create cron job entry
CRON_ENTRY="0 * * * * cd $CURRENT_DIR && python3 run_scrapers.py >> scraper.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_scrapers.py"; then
    echo "Cron job already exists. Updating..."
    # Remove existing entry and add new one
    (crontab -l 2>/dev/null | grep -v "run_scrapers.py"; echo "$CRON_ENTRY") | crontab -
else
    echo "Adding new cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
fi

# Verify cron job was added
if crontab -l 2>/dev/null | grep -q "run_scrapers.py"; then
    echo "✅ Cron job added successfully!"
    echo "The vulnerability scanner will run every hour."
    echo ""
    echo "To view current cron jobs: crontab -l"
    echo "To remove the cron job: crontab -e (then delete the line)"
    echo ""
    echo "Logs will be written to: $CURRENT_DIR/scraper.log"
else
    echo "❌ Failed to add cron job"
    exit 1
fi

# Create log file
touch scraper.log
echo "Created log file: scraper.log"

# Set up environment file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "Created .env file from template. Please edit it with your email settings."
    else
        echo "Warning: env.example not found. You may need to create .env manually."
    fi
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your email configuration"
echo "2. Run 'streamlit run app.py' to start the web interface"
echo "3. Access the dashboard at http://localhost:8501"
echo "4. The scanner will run automatically every hour"
echo ""
echo "Manual commands:"
echo "- Run scanner manually: python3 run_scrapers.py"
echo "- Run specific OEM: python3 run_scrapers.py microsoft"
echo "- View logs: tail -f scraper.log"
echo "- Check cron jobs: crontab -l"
