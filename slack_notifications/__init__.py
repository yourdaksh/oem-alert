"""
Slack notification system for vulnerability alerts
"""
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from config import SLACK_CONFIG
from database.operations import DatabaseOperations
from database.models import Vulnerability, Subscription

logger = logging.getLogger(__name__)

class SlackNotificationService:
    """Service for sending vulnerability alerts to Slack"""
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db_ops = db_ops
        self.slack_config = SLACK_CONFIG
        self.default_webhook_url = self.slack_config.get('webhook_url', '')
        self.default_channel = self.slack_config.get('default_channel', '#vulnerability-alerts')
        self.enabled = self.slack_config.get('enabled', False)
    
    def send_vulnerability_alert(self, subscription: Subscription, 
                               vulnerability: Vulnerability) -> bool:
        """Send a vulnerability alert to Slack"""
        try:
            webhook_url = subscription.slack_webhook_url if hasattr(subscription, 'slack_webhook_url') and subscription.slack_webhook_url else self.default_webhook_url
            
            if not webhook_url:
                logger.warning("No Slack webhook URL configured")
                return False
            
            message = self._create_slack_message(vulnerability)
            
            success = self._send_slack_message(webhook_url, message)
            
            self.db_ops.log_notification(
                subscription_id=subscription.id,
                vulnerability_id=vulnerability.id,
                slack_sent=success
            )
            
            if success:
                logger.info(f"Sent Slack vulnerability alert for {vulnerability.unique_id}")
            else:
                logger.error(f"Failed to send Slack vulnerability alert for {vulnerability.unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Slack vulnerability alert: {e}")
            self.db_ops.log_notification(
                subscription_id=subscription.id,
                vulnerability_id=vulnerability.id,
                slack_sent=False,
                error_message=str(e)
            )
            return False
    
    def send_bulk_vulnerability_alerts(self, vulnerability: Vulnerability) -> Dict[str, int]:
        """Send vulnerability alerts to all matching Slack subscribers"""
        subscriptions = self.db_ops.get_subscriptions_for_vulnerability(vulnerability)
        
        slack_subscriptions = [sub for sub in subscriptions 
                              if hasattr(sub, 'slack_webhook_url') and sub.slack_webhook_url]
        
        sent_count = 0
        failed_count = 0
        
        for subscription in slack_subscriptions:
            try:
                success = self.send_vulnerability_alert(subscription, vulnerability)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error sending Slack alert: {e}")
                failed_count += 1
        
        logger.info(f"Slack bulk alert results: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
    
    def _create_slack_message(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Create Slack message payload for vulnerability alert"""
        severity_color = {
            'Critical': '#ff3333',  # Red
            'High': '#ff6666',      # Light Red
            'Medium': '#ffcc00',    # Amber
            'Low': '#00ff41',       # Neon Green
            'Unknown': '#cccccc'    # Gray
        }.get(vulnerability.severity_level, '#cccccc')
        
        fields = [
            {
                "title": "Product",
                "value": vulnerability.product_name,
                "short": True
            },
            {
                "title": "OEM",
                "value": vulnerability.oem_name,
                "short": True
            },
            {
                "title": "Severity",
                "value": vulnerability.severity_level,
                "short": True
            },
            {
                "title": "CVSS Score",
                "value": vulnerability.cvss_score or "N/A",
                "short": True
            }
        ]
        
        if vulnerability.product_version:
            fields.append({
                "title": "Version",
                "value": vulnerability.product_version,
                "short": True
            })
        
        fields.append({
            "title": "Published Date",
            "value": vulnerability.published_date.strftime('%Y-%m-%d %H:%M:%S'),
            "short": True
        })
        
        attachment = {
            "color": severity_color,
            "title": f"{vulnerability.severity_level} Vulnerability: {vulnerability.unique_id}",
            "title_link": vulnerability.source_url if vulnerability.source_url else None,
            "text": vulnerability.vulnerability_description[:500] + "..." if len(vulnerability.vulnerability_description) > 500 else vulnerability.vulnerability_description,
            "fields": fields,
            "footer": "Vulnerability Scrapper",
            "ts": int(vulnerability.published_date.timestamp())
        }
        
        if vulnerability.mitigation_strategy:
            attachment["fields"].append({
                "title": "Mitigation Strategy",
                "value": vulnerability.mitigation_strategy[:200] + "..." if len(vulnerability.mitigation_strategy) > 200 else vulnerability.mitigation_strategy,
                "short": False
            })
        
        if vulnerability.source_url:
            attachment["fields"].append({
                "title": "Source",
                "value": vulnerability.source_url,
                "short": False
            })
        
        message = {
            "text": f"🚨 New {vulnerability.severity_level} Vulnerability Alert",
            "attachments": [attachment]
        }
        
        return message
    
    def _send_slack_message(self, webhook_url: str, message: Dict[str, Any]) -> bool:
        """Send message to Slack via webhook"""
        try:
            response = requests.post(
                webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Slack webhook returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack message: {e}")
            return False
    
    def test_slack_configuration(self, webhook_url: Optional[str] = None) -> bool:
        """Test Slack configuration by sending a test message"""
        try:
            test_webhook = webhook_url or self.default_webhook_url
            
            if not test_webhook:
                logger.error("No Slack webhook URL configured")
                return False
            
            test_message = {
                "text": "✅ Vulnerability Scrapper - Test Message",
                "attachments": [{
                    "color": "#00ff41",
                    "title": "Slack Integration Test",
                    "text": f"This is a test message from the Vulnerability Scrapper.\n\nIf you receive this message, your Slack configuration is working correctly.",
                    "footer": "Vulnerability Scrapper",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            success = self._send_slack_message(test_webhook, test_message)
            
            if success:
                logger.info("Slack configuration test successful")
            else:
                logger.error("Slack configuration test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Slack configuration test error: {e}")
            return False

def create_slack_service(db_ops: DatabaseOperations) -> SlackNotificationService:
    """Create and return a new SlackNotificationService instance"""
    return SlackNotificationService(db_ops)
