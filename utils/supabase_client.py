"""
Supabase client utility for authentication and real-time features
"""
import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured. Supabase features will be disabled.")
        return None
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def is_supabase_enabled() -> bool:
    """Check if Supabase is configured and enabled"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return bool(supabase_url and supabase_key)

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with Supabase"""
    if not is_supabase_enabled():
        logger.warning("Supabase authentication not available - using fallback")
        return None
    
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "user": response.user,
                "session": response.session
            }
        return None
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

def sign_up_user(email: str, password: str, metadata: Optional[Dict[str, Any]] = None, redirect_to: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Sign up a new user with Supabase"""
    if not is_supabase_enabled():
        return None
    
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        sign_up_data = {
            "email": email,
            "password": password
        }
        
        if metadata:
            sign_up_data["data"] = metadata
        
        if redirect_to:
            sign_up_data["options"] = {
                "email_redirect_to": redirect_to
            }
        else:
            sign_up_data["options"] = {
                "email_redirect_to": "http://localhost:8501"
            }
        
        response = client.auth.sign_up(sign_up_data)
        
        if response.user:
            return {
                "user": response.user,
                "session": response.session
            }
        return None
    except Exception as e:
        logger.error(f"Sign up failed: {e}")
        return None

def sign_out_user(session_token: str) -> bool:
    """Sign out user from Supabase"""
    if not is_supabase_enabled():
        return False
    
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.auth.set_session(access_token=session_token, refresh_token="")
        client.auth.sign_out()
        return True
    except Exception as e:
        logger.error(f"Sign out failed: {e}")
        return False

def get_user_from_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Get user information from session token"""
    if not is_supabase_enabled():
        return None
    
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.auth.get_user(session_token)
        if response.user:
            return {
                "user": response.user
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get user from session: {e}")
        return None
