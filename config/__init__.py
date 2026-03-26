"""
Configuration management for the Vulnerability Scrapper system
"""
import yaml
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

def load_oems_config() -> Dict[str, Any]:
    """Load OEM configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'oems.yaml')
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config.get('oems_config', {})
    except FileNotFoundError:
        try:
            from config.oems import oems_config
            return oems_config
        except ImportError:
            return {}
    except Exception as e:
        print(f"Error loading OEM config: {e}")
        return {}

def get_enabled_oems() -> List[str]:
    """Get list of enabled OEMs"""
    config = load_oems_config()
    return [oem_id for oem_id, oem_config in config.items() 
            if oem_config.get('enabled', True)]

def get_oem_config(oem_id: str) -> Dict[str, Any]:
    """Get configuration for a specific OEM"""
    config = load_oems_config()
    return config.get(oem_id, {})

def get_all_oems() -> Dict[str, Any]:
    """Get all OEM configurations"""
    return load_oems_config()

EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email_username": os.getenv("EMAIL_USERNAME", ""),
    "email_password": os.getenv("EMAIL_PASSWORD", ""),
    "from_email": os.getenv("FROM_EMAIL", ""),
    "use_tls": True
}

SLACK_CONFIG = {
    "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
    "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
    "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", "#vulnerability-alerts")
}

APP_CONFIG = {
    "database_url": os.getenv("SUPABASE_DB_URL"),
    "scan_interval_minutes": 60,  # Default scan interval
    "max_vulnerabilities_per_scan": 1000,
    "email_batch_size": 50,
    "log_level": "INFO",
    "debug_mode": False
}

STREAMLIT_CONFIG = {
    "page_title": "Vulnerability Scper Platform",

    "page_icon": "🚨",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
