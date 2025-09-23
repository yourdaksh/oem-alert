# 📧 Email Configuration Guide

## Quick Setup

### Option 1: Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Copy the 16-character password

3. **Update .env file**:
```bash
# Edit the .env file
nano .env

# Update these lines:
EMAIL_USERNAME=your-actual-email@gmail.com
EMAIL_PASSWORD=your-16-character-app-password
FROM_EMAIL=your-actual-email@gmail.com
```

### Option 2: Other Email Providers

**Outlook/Hotmail:**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
```

**Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
```

**Custom SMTP:**
```bash
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@company.com
EMAIL_PASSWORD=your-password
```

## Automated Setup

Run the setup script:
```bash
./setup_email.sh
```

## Test Email Configuration

After updating .env, test the configuration:
```bash
source venv/bin/activate
python3 -c "
from email_notifications import EmailNotifier
notifier = EmailNotifier()
result = notifier.test_configuration()
print('✅ Email test successful!' if result else '❌ Email test failed')
"
```

## Features

Once configured, you can:
- Set up email subscriptions in the web interface
- Receive alerts for new vulnerabilities
- Configure notification preferences by OEM
- Get daily/weekly vulnerability summaries

## Troubleshooting

**Gmail Issues:**
- Make sure 2FA is enabled
- Use App Password, not regular password
- Check if "Less secure app access" is enabled (if not using App Password)

**General Issues:**
- Check firewall settings
- Verify SMTP server and port
- Test with a simple email client first
