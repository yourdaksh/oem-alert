from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import List, Optional
from backend.dependencies import get_supabase, get_current_user
from backend.models_pydantic import VulnerabilityOut

router = APIRouter(prefix="/vulnerabilities", tags=["Vulnerabilities"])

@router.get("/", response_model=List[VulnerabilityOut])
async def get_vulnerabilities(
    oem: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, le=500),
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Fetch vulnerabilities with optional filtering. Requires authentication."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection missing")
        
    query = supabase.table("vulnerabilities").select("*")
    
    if oem:
        query = query.eq("oem_name", oem)
    if severity:
        query = query.eq("severity_level", severity)
        
    res = query.order("published_date", desc=True).limit(limit).execute()
    
    return res.data

@router.get("/{vuln_id}", response_model=VulnerabilityOut)
async def get_vulnerability(
    vuln_id: str,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Retrieve a single vulnerability by UUID."""
    res = supabase.table("vulnerabilities").select("*").eq("id", vuln_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
        
    return res.data[0]
