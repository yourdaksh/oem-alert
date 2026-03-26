
import requests
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

def send_slack_alert(webhook_url: str, vulnerability: Any) -> bool:
    """
    Send a Slack alert for a vulnerability.
    """
    if not webhook_url:
        return False
        
    try:
        payload = {
            "text": f"🚨 *CRITICAL VULNERABILITY DETECTED* 🚨\n\n*Product:* {vulnerability.product_name}\n*OEM:* {vulnerability.oem_name}\n*ID:* {vulnerability.unique_id}\n*CVSS:* {vulnerability.cvss_score}\n\n<{vulnerability.source_url}|View Details>"
        }
        
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Slack alert sent for {vulnerability.unique_id}")
            return True
        else:
            logger.error(f"Failed to send Slack alert. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        return False
