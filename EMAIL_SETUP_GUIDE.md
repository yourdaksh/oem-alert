# 📧 Email Configuration Setup Guide

This guide will help you configure email notifications for the Vulnerability Scrapper.

## Quick Setup (Gmail - Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. Still in **Security** settings
2. Scroll down to **2-Step Verification** section
3. Click on **App passwords** (you may need to sign in again)
4. Select **Mail** as the app type
5. Select **Other (Custom name)** as the device
6. Enter a name like "Vulnerability Scrapper"
7. Click **Generate**
8. **Copy the 16-character password** (you'll see it only once!)

### Step 3: Configure .env File
1. Open your `.env` file in the project directory
2. Update these lines with your Gmail credentials:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
FROM_EMAIL=your-email@gmail.com
```

**Important:** 
- Use the **16-character App Password** (not your regular Gmail password)
- The App Password has spaces, but you can include them or remove them - both work
- Example: `EMAIL_PASSWORD=abcd efgh ijkl mnop` or `EMAIL_PASSWORD=abcdefghijklmnop`

### Step 4: Test Email Configuration

**Option A: Using the Web Interface**
1. Start your Streamlit app: `streamlit run app.py`
2. Navigate to **Settings** in the sidebar
3. Click **"Test Email Configuration"** button
4. Check your email inbox for the test message

**Option B: Using Command Line**
```bash
cd /Users/dakshpatil/Downloads/oem-alert-1
python3 << 'EOF'
from database import get_db, init_database
from database.operations import DatabaseOperations
from email_notifications import create_email_service

init_database()
db = next(get_db())
db_ops = DatabaseOperations(db)
email_service = create_email_service(db_ops)

success = email_service.test_email_configuration()
if success:
    print("✅ Email configuration test successful!")
    print("Check your inbox for the test email.")
else:
    print("❌ Email configuration test failed.")
    print("Please check your .env file settings.")
EOF
```

## Alternative Email Providers

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
FROM_EMAIL=your-email@outlook.com
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@yahoo.com
```

**Note:** Yahoo also requires an App Password. Generate it at: [Yahoo Account Security](https://login.yahoo.com/account/security)

### Custom SMTP Server
```bash
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@company.com
EMAIL_PASSWORD=your-password
FROM_EMAIL=your-email@company.com
```

## Complete .env Example

Here's a complete example of email configuration in your `.env` file:

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=yourname@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
FROM_EMAIL=yourname@gmail.com

# Other configurations...
DATABASE_TYPE=sqlite
# ... rest of your config
```

## Using Email Subscriptions

Once email is configured, you can:

1. **Add Email Subscriptions:**
   - Go to **Email & Slack Subscription Management** in the app
   - Click **"Add New Subscription"**
   - Select **"Email"** as notification type
   - Enter your email address
   - Configure filters (OEM, severity levels, etc.)
   - Click **"Add Subscription"**

2. **Receive Alerts:**
   - When new vulnerabilities are found that match your subscription criteria
   - You'll receive formatted email alerts with:
     - Vulnerability details
     - Severity level
     - CVSS scores
     - Mitigation strategies
     - Links to source information

## Troubleshooting

### Issue: "Email credentials not configured"
**Solution:** Make sure all email fields in `.env` are filled:
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `SMTP_SERVER`
- `SMTP_PORT`

### Issue: "Authentication failed" or "Login failed"
**Solution for Gmail:**
- Make sure you're using an **App Password**, not your regular password
- Verify 2-Factor Authentication is enabled
- Check that the App Password was copied correctly (no extra spaces)

### Issue: "Connection refused" or "Connection timeout"
**Solution:**
- Check your firewall settings
- Verify SMTP server and port are correct
- Try port 465 with SSL instead of 587 with TLS

### Issue: Test email not received
**Solution:**
- Check spam/junk folder
- Verify email address is correct
- Check email service logs in the terminal
- Try sending to a different email address

### Issue: "Less secure app access" error (Gmail)
**Solution:**
- Google no longer supports "Less secure app access"
- You **must** use App Passwords with 2FA enabled
- Follow the App Password setup steps above

## Security Best Practices

1. **Never commit `.env` file to git** - it contains sensitive credentials
2. **Use App Passwords** instead of your main password
3. **Rotate App Passwords** periodically
4. **Use environment variables** in production instead of `.env` files
5. **Limit email subscriptions** to trusted recipients

## Production Setup

For production environments:

1. Use environment variables instead of `.env`:
   ```bash
   export EMAIL_USERNAME=your-email@company.com
   export EMAIL_PASSWORD=your-app-password
   export SMTP_SERVER=smtp.company.com
   export SMTP_PORT=587
   ```

2. Use a dedicated email service account (not personal email)

3. Configure proper SPF/DKIM records for your domain

4. Monitor email delivery rates

5. Set up email bounce handling

## Need Help?

If you're still having issues:
1. Check the terminal/console for error messages
2. Verify your email provider's SMTP settings
3. Test with a simple email client first
4. Check firewall/network restrictions

---

**Quick Reference:**
- Gmail SMTP: `smtp.gmail.com:587`
- Outlook SMTP: `smtp-mail.outlook.com:587`
- Yahoo SMTP: `smtp.mail.yahoo.com:587`
