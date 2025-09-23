# OEM Vulnerability Alert Platform - Complete Usage Guide

## 🚀 Quick Start Commands

### 1. Initial Setup
```bash
# Navigate to project directory
cd /home/spartan/Downloads/oem-alert

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not done)
pip install -r requirements.txt

# Initialize database
python3 setup_database.py setup

# Set up cron job (every hour by default)
./setup.sh
```

### 2. Running the Web Interface
```bash
# Start Streamlit dashboard
streamlit run app.py

# Access at: http://localhost:8501
# Or with custom port: streamlit run app.py --server.port 8502
```

### 3. Manual Scanning
```bash
# Scan all OEMs
python3 run_scrapers.py

# Scan specific OEM
python3 run_scrapers.py microsoft
python3 run_scrapers.py ubuntu
python3 run_scrapers.py cisco
```

## ⏰ Cron Job Management

### View Current Cron Jobs
```bash
# List all cron jobs
crontab -l

# Check if our job exists
crontab -l | grep "run_scrapers.py"
```

### Change Scanning Schedule
```bash
# Use interactive script
./change_schedule.sh

# Or edit config manually
nano cron_schedule.conf
# Change: SCHEDULE="0 */2 * * *"  # Every 2 hours
./setup.sh  # Re-apply changes
```

### Remove Cron Job
```bash
# Remove all cron jobs
crontab -r

# Remove only our job
crontab -l | grep -v "run_scrapers.py" | crontab -
```

## 📊 Monitoring & Logs

### View Scan Logs
```bash
# View recent logs
tail -f scraper.log

# View last 50 lines
tail -50 scraper.log

# Search for errors
grep -i error scraper.log

# Search for specific OEM
grep -i "ubuntu" scraper.log
```

### Check System Status
```bash
# Check if cron service is running
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/cron

# Check system logs for cron
sudo journalctl -u cron -f
```

## 🔧 Advanced Configuration

### Custom Cron Schedules
```bash
# Edit cron directly
crontab -e

# Add custom entry
# Every 15 minutes: */15 * * * * cd /path/to/project && python3 run_scrapers.py >> scraper.log 2>&1
# Daily at 3 AM: 0 3 * * * cd /path/to/project && python3 run_scrapers.py >> scraper.log 2>&1
# Weekdays at 9 AM: 0 9 * * 1-5 cd /path/to/project && python3 run_scrapers.py >> scraper.log 2>&1
```

### Environment Variables
```bash
# Copy example environment file
cp env.example .env

# Edit email settings
nano .env
```

## 🧪 Testing & Debugging

### Test Individual Components
```bash
# Test database
python3 test_system.py

# Test with mock data
python3 test_mock_data.py

# Test scraping workflow
python3 test_scraping_workflow.py
```

### Debug Cron Issues
```bash
# Check cron syntax
crontab -l

# Test cron job manually
cd /home/spartan/Downloads/oem-alert && python3 run_scrapers.py

# Check file permissions
ls -la run_scrapers.py
ls -la scraper.log
```

## 📱 Remote Access

### Access from Other Devices
```bash
# Find your IP address
ip addr show | grep inet

# Start Streamlit with network access
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Access from other devices: http://YOUR_IP:8501
```

## 🔄 Maintenance Commands

### Update Dependencies
```bash
# Update Python packages
pip install -r requirements.txt --upgrade

# Check for outdated packages
pip list --outdated
```

### Database Maintenance
```bash
# Backup database
cp vulnerability_alerts.db vulnerability_alerts_backup.db

# Reset database (WARNING: deletes all data)
python3 setup_database.py reset
```

### Log Management
```bash
# Rotate logs (keep last 1000 lines)
tail -1000 scraper.log > scraper.log.tmp && mv scraper.log.tmp scraper.log

# Archive old logs
mv scraper.log scraper_$(date +%Y%m%d).log
touch scraper.log
```

## 🚨 Troubleshooting

### Common Issues
```bash
# Permission denied
chmod +x setup.sh
chmod +x change_schedule.sh

# Python not found
which python3
# If not found: sudo apt install python3 python3-pip

# Virtual environment issues
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check System Resources
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep python
ps aux | grep streamlit
```

## 📋 Quick Reference

| Command | Purpose |
|---------|---------|
| `./setup.sh` | Initial setup with cron job |
| `./change_schedule.sh` | Change scanning frequency |
| `streamlit run app.py` | Start web dashboard |
| `python3 run_scrapers.py` | Manual scan all OEMs |
| `crontab -l` | View cron jobs |
| `tail -f scraper.log` | Monitor logs |
| `source venv/bin/activate` | Activate virtual environment |
