#!/bin/bash

# OEM Alert - Schedule Management Script
# This script helps you easily change the scanning frequency

echo "🕒 OEM Vulnerability Alert - Schedule Manager"
echo "=============================================="
echo ""

# Function to show current schedule
show_current_schedule() {
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "run_scrapers.py" || echo "No cron job found"
    echo ""
}

# Function to update schedule
update_schedule() {
    local new_schedule="$1"
    local description="$2"
    
    echo "Updating schedule to: $description"
    echo "Schedule: $new_schedule"
    
    # Update the config file
    sed -i "s/^SCHEDULE=.*/SCHEDULE=\"$new_schedule\"/" cron_schedule.conf
    
    # Re-run setup to update cron job
    ./setup.sh
    
    echo "✅ Schedule updated successfully!"
    echo ""
}

# Show current status
show_current_schedule

# Interactive menu
echo "Choose a new scanning schedule:"
echo "1) Every 30 minutes (frequent monitoring)"
echo "2) Every hour (current default)"
echo "3) Every 2 hours"
echo "4) Every 6 hours"
echo "5) Daily at 2 AM (light monitoring)"
echo "6) Weekdays at 9 AM (business hours)"
echo "7) Twice daily (6 AM and 6 PM)"
echo "8) Custom schedule"
echo "9) Remove cron job"
echo "0) Exit"
echo ""

read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        update_schedule "*/30 * * * *" "Every 30 minutes"
        ;;
    2)
        update_schedule "0 * * * *" "Every hour"
        ;;
    3)
        update_schedule "0 */2 * * *" "Every 2 hours"
        ;;
    4)
        update_schedule "0 */6 * * *" "Every 6 hours"
        ;;
    5)
        update_schedule "0 2 * * *" "Daily at 2 AM"
        ;;
    6)
        update_schedule "0 9 * * 1-5" "Weekdays at 9 AM"
        ;;
    7)
        update_schedule "0 6,18 * * *" "Twice daily (6 AM and 6 PM)"
        ;;
    8)
        echo ""
        echo "Enter custom cron schedule (format: minute hour day month weekday)"
        echo "Examples:"
        echo "  */15 * * * *     (every 15 minutes)"
        echo "  0 8 * * 1       (Mondays at 8 AM)"
        echo "  30 2 * * 1-5    (weekdays at 2:30 AM)"
        echo ""
        read -p "Custom schedule: " custom_schedule
        if [[ -n "$custom_schedule" ]]; then
            update_schedule "$custom_schedule" "Custom: $custom_schedule"
        else
            echo "❌ Invalid schedule"
        fi
        ;;
    9)
        echo "Removing cron job..."
        crontab -l 2>/dev/null | grep -v "run_scrapers.py" | crontab -
        echo "✅ Cron job removed"
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Useful commands:"
echo "  View cron jobs: crontab -l"
echo "  View logs: tail -f scraper.log"
echo "  Manual scan: python3 run_scrapers.py"
echo "  Start web UI: streamlit run app.py"
