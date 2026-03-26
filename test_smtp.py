import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_username = os.getenv("EMAIL_USERNAME")
smtp_password = os.getenv("EMAIL_PASSWORD")
from_email = os.getenv("FROM_EMAIL", smtp_username)

print(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
print(f"Username: {smtp_username}")

if not smtp_username or not smtp_password or smtp_username == 'your-email@gmail.com':
    print("Error: EMAIL_USERNAME or EMAIL_PASSWORD not properly configured in environment.")
    exit(1)

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    
    server.quit()
    print("Success: SMTP authentication works!")
except Exception as e:
    print(f"Failed to connect or authenticate. Error: {e}")

