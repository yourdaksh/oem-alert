#!/bin/bash

echo "📧 Email Configuration Setup for Vulnerability Scrapper"
echo "================================================================="
echo ""
echo "This script will help you configure email notifications."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup first."
    exit 1
fi

echo "Current email configuration:"
echo "---------------------------"
grep -E "EMAIL_|SMTP_" .env
echo ""

echo "📋 Email Setup Instructions:"
echo "============================"
echo ""
echo "1. Gmail Setup (Recommended):"
echo "   - Enable 2-Factor Authentication on your Gmail account"
echo "   - Go to Google Account → Security → 2-Step Verification → App passwords"
echo "   - Generate an App Password for 'Mail'"
echo "   - Copy the 16-character password"
echo ""
echo "2. Alternative Email Providers:"
echo "   - Outlook/Hotmail: smtp-mail.outlook.com:587"
echo "   - Yahoo: smtp.mail.yahoo.com:587"
echo "   - Custom SMTP: Use your organization's SMTP server"
echo ""

read -p "Enter your email address: " email
read -p "Enter your email password (or App Password for Gmail): " password
read -p "Enter SMTP server (default: smtp.gmail.com): " smtp_server
read -p "Enter SMTP port (default: 587): " smtp_port

# Set defaults
smtp_server=${smtp_server:-smtp.gmail.com}
smtp_port=${smtp_port:-587}

echo ""
echo "Updating .env file with your email configuration..."

# Backup original .env
cp .env .env.backup

# Update email settings
sed -i "s/EMAIL_USERNAME=.*/EMAIL_USERNAME=$email/" .env
sed -i "s/EMAIL_PASSWORD=.*/EMAIL_PASSWORD=$password/" .env
sed -i "s/FROM_EMAIL=.*/FROM_EMAIL=$email/" .env
sed -i "s/SMTP_SERVER=.*/SMTP_SERVER=$smtp_server/" .env
sed -i "s/SMTP_PORT=.*/SMTP_PORT=$smtp_port/" .env

echo "✅ Email configuration updated!"
echo ""
echo "Updated settings:"
echo "----------------"
grep -E "EMAIL_|SMTP_" .env
echo ""

echo "🧪 Testing email configuration..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Test email configuration
try:
    from email_notifications import EmailNotifier
    notifier = EmailNotifier()
    result = notifier.test_configuration()
    if result:
        print('✅ Email configuration test successful!')
    else:
        print('❌ Email configuration test failed. Please check your credentials.')
except Exception as e:
    print(f'❌ Error testing email configuration: {e}')
"

echo ""
echo "📧 Email notifications are now configured!"
echo "You can:"
echo "- Set up email subscriptions in the web interface"
echo "- Receive alerts for new vulnerabilities"
echo "- Configure notification preferences"
echo ""
echo "🌐 Access your platform at: http://localhost:8501"
