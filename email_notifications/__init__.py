"""
Email notification system for vulnerability alerts
"""
import smtplib
import yagmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from config import EMAIL_CONFIG
from database.operations import DatabaseOperations
from database.models import Vulnerability, Subscription

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service for sending vulnerability alert emails"""
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db_ops = db_ops
        self.email_config = EMAIL_CONFIG
        self.smtp_server = self.email_config['smtp_server']
        self.smtp_port = self.email_config['smtp_port']
        self.email_username = self.email_config['email_username']
        self.email_password = self.email_config['email_password']
        self.from_email = self.email_config['from_email'] or self.email_username
        self.use_tls = self.email_config['use_tls']
    
    def send_vulnerability_alert(self, subscription: Subscription, 
                               vulnerability: Vulnerability) -> bool:
        """Send a vulnerability alert email to a subscriber"""
        try:
            # Create email content
            subject = f"🚨 {vulnerability.severity_level} Vulnerability Alert: {vulnerability.product_name}"
            html_content = self._create_vulnerability_email_html(vulnerability)
            text_content = self._create_vulnerability_email_text(vulnerability)
            
            # Send email
            success = self._send_email(
                to_email=subscription.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log the notification
            self.db_ops.log_notification(
                subscription_id=subscription.id,
                vulnerability_id=vulnerability.id,
                email_sent=success
            )
            
            if success:
                logger.info(f"Sent vulnerability alert to {subscription.email}")
            else:
                logger.error(f"Failed to send vulnerability alert to {subscription.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending vulnerability alert: {e}")
            # Log the failed notification
            self.db_ops.log_notification(
                subscription_id=subscription.id,
                vulnerability_id=vulnerability.id,
                email_sent=False,
                error_message=str(e)
            )
            return False
    
    def send_bulk_vulnerability_alerts(self, vulnerability: Vulnerability) -> Dict[str, int]:
        """Send vulnerability alerts to all matching subscribers"""
        # Get all subscriptions that match this vulnerability
        subscriptions = self.db_ops.get_subscriptions_for_vulnerability(vulnerability)
        
        sent_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            try:
                success = self.send_vulnerability_alert(subscription, vulnerability)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error sending alert to {subscription.email}: {e}")
                failed_count += 1
        
        logger.info(f"Bulk alert results: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
    
    def _create_vulnerability_email_html(self, vulnerability: Vulnerability) -> str:
        """Create HTML content for vulnerability email"""
        severity_color = {
            'Critical': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745',
            'Unknown': '#6c757d'
        }.get(vulnerability.severity_level, '#6c757d')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Vulnerability Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {severity_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .vulnerability-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .severity-badge {{ background-color: {severity_color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .footer {{ background-color: #e9ecef; padding: 15px; text-align: center; font-size: 12px; }}
                .button {{ background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Vulnerability Alert</h1>
                <p>OEM Vulnerability Alert Platform</p>
            </div>
            
            <div class="content">
                <h2>New {vulnerability.severity_level} Vulnerability Detected</h2>
                
                <div class="vulnerability-info">
                    <h3>Vulnerability Details</h3>
                    <p><strong>Unique ID:</strong> {vulnerability.unique_id}</p>
                    <p><strong>Product:</strong> {vulnerability.product_name}</p>
                    <p><strong>Version:</strong> {vulnerability.product_version or 'Not specified'}</p>
                    <p><strong>OEM:</strong> {vulnerability.oem_name}</p>
                    <p><strong>Severity:</strong> <span class="severity-badge">{vulnerability.severity_level}</span></p>
                    <p><strong>CVSS Score:</strong> {vulnerability.cvss_score or 'Not available'}</p>
                    <p><strong>Published Date:</strong> {vulnerability.published_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="vulnerability-info">
                    <h3>Description</h3>
                    <p>{vulnerability.vulnerability_description}</p>
                </div>
                
                {f'<div class="vulnerability-info"><h3>Mitigation Strategy</h3><p>{vulnerability.mitigation_strategy}</p></div>' if vulnerability.mitigation_strategy else ''}
                
                {f'<div class="vulnerability-info"><h3>Affected Versions</h3><p>{vulnerability.affected_versions}</p></div>' if vulnerability.affected_versions else ''}
                
                {f'<p><a href="{vulnerability.source_url}" class="button">View Full Details</a></p>' if vulnerability.source_url else ''}
            </div>
            
            <div class="footer">
                <p>This alert was sent by the OEM Vulnerability Alert Platform</p>
                <p>To unsubscribe or modify your preferences, please visit the platform dashboard</p>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_vulnerability_email_text(self, vulnerability: Vulnerability) -> str:
        """Create plain text content for vulnerability email"""
        lines = [
            "VULNERABILITY ALERT",
            "==================",
            "",
            f"New {vulnerability.severity_level} Vulnerability Detected",
            "",
            "Vulnerability Details:",
            f"- Unique ID: {vulnerability.unique_id}",
            f"- Product: {vulnerability.product_name}",
            f"- Version: {vulnerability.product_version or 'Not specified'}",
            f"- OEM: {vulnerability.oem_name}",
            f"- Severity: {vulnerability.severity_level}",
            f"- CVSS Score: {vulnerability.cvss_score or 'Not available'}",
            f"- Published Date: {vulnerability.published_date.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Description:",
            vulnerability.vulnerability_description or "",
            ""
        ]

        if vulnerability.mitigation_strategy:
            lines.append("Mitigation Strategy:")
            lines.append(vulnerability.mitigation_strategy)
            lines.append("")

        if vulnerability.affected_versions:
            lines.append("Affected Versions:")
            lines.append(vulnerability.affected_versions)
            lines.append("")

        if vulnerability.source_url:
            lines.append("Full Details:")
            lines.append(vulnerability.source_url)
            lines.append("")

        lines.append("---")
        lines.append("This alert was sent by the OEM Vulnerability Alert Platform")
        lines.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)
    
    def _send_email(self, to_email: str, subject: str, 
                   html_content: str, text_content: str) -> bool:
        """Send email using SMTP"""
        try:
            if not self.email_username or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
            # Try using yagmail first (simpler)
            try:
                yag = yagmail.SMTP(self.email_username, self.email_password)
                yag.send(
                    to=to_email,
                    subject=subject,
                    contents=[text_content, html_content]
                )
                yag.close()
                return True
            except Exception as e:
                logger.warning(f"yagmail failed, trying SMTP: {e}")
            
            # Fallback to SMTP
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def test_email_configuration(self) -> bool:
        """Test email configuration by sending a test email"""
        try:
            if not self.email_username or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
            test_subject = "OEM Vulnerability Alert Platform - Test Email"
            test_content = """
            This is a test email from the OEM Vulnerability Alert Platform.
            
            If you receive this email, your email configuration is working correctly.
            
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            success = self._send_email(
                to_email=self.email_username,  # Send to self for testing
                subject=test_subject,
                html_content=test_content,
                text_content=test_content
            )
            
            if success:
                logger.info("Email configuration test successful")
            else:
                logger.error("Email configuration test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Email configuration test error: {e}")
            return False

def create_email_service(db_ops: DatabaseOperations) -> EmailNotificationService:
    """Create and return a new EmailNotificationService instance"""
    return EmailNotificationService(db_ops)
