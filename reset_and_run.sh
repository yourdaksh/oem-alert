#!/bin/bash

# Reset and Run Script for Vulnerability Scraper

echo "🔄 Resetting Database..."

# Stop any running instances
pkill -f "streamlit" 2>/dev/null || true

# Remove old databases
rm -f vulnerability_alerts.db
rm -f temp_vulnerability_alerts.db
rm -f vulnerability_alerts.db-shm
rm -f vulnerability_alerts.db-wal

echo "✅ Old databases removed"

# Initialize fresh database
echo "🔧 Creating fresh database..."
python3 setup_database.py

echo "✅ Database initialized"

# Run the application
echo "🚀 Starting Vulnerability Scraper..."
./run.sh
