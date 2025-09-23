#!/bin/bash

# OEM Alert - Quick Management Script
# Run this script from anywhere to manage your OEM Alert system

PROJECT_DIR="/home/spartan/Downloads/oem-alert"

echo "🔧 OEM Vulnerability Alert - Quick Manager"
echo "=========================================="
echo ""

# Function to run commands in project directory
run_in_project() {
    cd "$PROJECT_DIR" && "$@"
}

# Function to show status
show_status() {
    echo "📊 System Status:"
    echo "  Project Directory: $PROJECT_DIR"
    echo "  Cron Jobs:"
    crontab -l 2>/dev/null | grep "run_scrapers.py" || echo "    No cron job found"
    echo "  Recent Logs:"
    if [ -f "$PROJECT_DIR/scraper.log" ]; then
        tail -3 "$PROJECT_DIR/scraper.log" | sed 's/^/    /'
    else
        echo "    No log file found"
    fi
    echo ""
}

# Main menu
while true; do
    show_status
    
    echo "Choose an action:"
    echo "1) Start Web Dashboard"
    echo "2) Run Manual Scan"
    echo "3) Change Schedule"
    echo "4) View Logs"
    echo "5) Check Cron Jobs"
    echo "6) Remove Cron Job"
    echo "7) Test System"
    echo "0) Exit"
    echo ""
    
    read -p "Enter choice (0-7): " choice
    
    case $choice in
        1)
            echo "Starting web dashboard..."
            run_in_project streamlit run app.py
            ;;
        2)
            echo "Running manual scan..."
            run_in_project python3 run_scrapers.py
            echo "Scan completed!"
            ;;
        3)
            echo "Opening schedule manager..."
            run_in_project ./change_schedule.sh
            ;;
        4)
            echo "Recent logs (press Ctrl+C to exit):"
            run_in_project tail -f scraper.log
            ;;
        5)
            echo "Current cron jobs:"
            crontab -l
            ;;
        6)
            echo "Removing cron job..."
            crontab -l 2>/dev/null | grep -v "run_scrapers.py" | crontab -
            echo "Cron job removed!"
            ;;
        7)
            echo "Testing system..."
            run_in_project python3 test_system.py
            ;;
        0)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done
