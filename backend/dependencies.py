from fastapi import HTTPException, Header
from supabase import create_client, Client
import os
from typing import Optional

def get_supabase() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        return None
        
    return create_client(supabase_url, supabase_key)

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        
    token = authorization.split(" ")[1]
    supabase = get_supabase()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
        
    try:
        res = supabase.auth.get_user(token)
        return res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
