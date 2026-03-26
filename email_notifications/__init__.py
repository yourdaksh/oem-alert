"""
Email notification system for vulnerability alerts
"""
import os
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
            subject = f"🚨 {vulnerability.severity_level} Vulnerability Alert: {vulnerability.product_name}"
            html_content = self._create_vulnerability_email_html(vulnerability)
            text_content = self._create_vulnerability_email_text(vulnerability)
            
            success = self._send_email(
                to_email=subscription.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
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
            self.db_ops.log_notification(
                subscription_id=subscription.id,
                vulnerability_id=vulnerability.id,
                email_sent=False,
                error_message=str(e)
            )
            return False
    
    def send_bulk_vulnerability_alerts(self, vulnerability: Vulnerability) -> Dict[str, int]:
        """Send vulnerability alerts to all matching subscribers"""
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
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color:
                .header {{ background-color: {severity_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .vulnerability-info {{ background-color:
                .severity-badge {{ background-color: {severity_color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .footer {{ background-color:
                .button {{ background-color:
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Vulnerability Alert</h1>
                <p>Vulnerability Scrapper</p>
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
                <p>This alert was sent by the Vulnerability Scrapper</p>
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
        lines.append("This alert was sent by the Vulnerability Scrapper")
        lines.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)
    
    def _send_email(self, to_email: str, subject: str, 
                   html_content: str, text_content: str) -> bool:
        """Send email using SMTP"""
        try:
            if not self.email_username or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
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
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
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
    
    def send_assignment_email(self, assignee_email: str, assignee_name: str, 
                            assigner_name: str, vulnerability_title: str, 
                            vulnerability_id: str, severity: str = "High") -> bool:
        """Send email notification for task assignment"""
        subject = f"ACTION REQUIRED: New Assignment - [{severity}] {vulnerability_title}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #00d4aa; margin-top: 0;">New Task Assignment</h2>
                <p>Hello <strong>{assignee_name}</strong>,</p>
                <p>You have been assigned a new vulnerability remediation task by <strong>{assigner_name}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #00d4aa; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{vulnerability_title}</h3>
                    <p style="margin-bottom: 5px;"><strong>ID:</strong> {vulnerability_id}</p>
                    <p style="margin-bottom: 5px;"><strong>Severity:</strong> {severity}</p>
                </div>
                
                <p>Please log in to the platform to investigate and resolve this issue.</p>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{os.environ.get('NEXT_PUBLIC_DASHBOARD_URL', 'https://oem-alert-dashboard.onrender.com')}/" style="background-color: #00d4aa; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Open Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        ACTION REQUIRED: New Assignment
        
        Hello {assignee_name},
        
        You have been assigned the following vulnerability by {assigner_name}:
        
        Task: {vulnerability_title}
        ID: {vulnerability_id}
        Severity: {severity}
        
        Please log in to {os.environ.get('NEXT_PUBLIC_DASHBOARD_URL', 'https://oem-alert-dashboard.onrender.com')}/ to take action.
        """
        
        return self._send_email(
            to_email=assignee_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    def send_invitation_email(self, email: str, invite_link: str, role: str) -> bool:
        """Send invitation email to new user"""
        subject = "🔑 Invitation to Join OEM Alert Platform"
        
        html_content = f"""
        <html>
        <body>
            <h2>You've been invited!</h2>
            <p>You have been invited to join the OEM Vulnerability Alert Platform as a <strong>{role}</strong>.</p>
            <p>Click the button below to set up your account and join your organization:</p>
            
            <p><a href="{invite_link}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
            
            <p>Or copy this link: {invite_link}</p>
            <p>This link will expire in 7 days.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        You've been invited!
        You have been invited to join the OEM Vulnerability Alert Platform as a {role}.
        Please visit the following link to accept:
        {invite_link}
        """
        
        return self._send_email(email, subject, html_content, text_content)

    def test_email_configuration(self) -> bool:
        """Test email configuration by sending a test email"""
        try:
            if not self.email_username or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
            from datetime import datetime
            
            test_subject = "Vulnerability Scrapper - Test Email"
            test_content = f"""
            This is a test email from the Vulnerability Scrapper.
            
            If you receive this email, your email configuration is working correctly.
            
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            logger.info(f"Testing email configuration for {self.email_username}")
            logger.info(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
            
            success = self._send_email(
                to_email=self.email_username,
                subject=test_subject,
                html_content=test_content,
                text_content=test_content
            )
            
            if success:
                logger.info(f"Email configuration test successful - email sent to {self.email_username}")
            else:
                logger.error("Email configuration test failed - _send_email returned False")
            
            return success
            
        except Exception as e:
            logger.error(f"Email configuration test error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def create_email_service(db_ops: DatabaseOperations) -> EmailNotificationService:
    """Create and return a new EmailNotificationService instance"""
    return EmailNotificationService(db_ops)
