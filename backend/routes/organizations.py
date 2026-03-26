from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Optional
from backend.dependencies import get_supabase, get_current_user
from backend.models_pydantic import OrganizationOut

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/me", response_model=OrganizationOut)
async def get_my_organization(
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Get the organization details for the current user."""
    user_db = supabase.table("users").select("organization_id").eq("id", user.id).execute()
    
    if not user_db.data or not user_db.data[0].get("organization_id"):
        raise HTTPException(status_code=404, detail="User is not linked to an organization")
        
    org_id = user_db.data[0]["organization_id"]
    org_res = supabase.table("organizations").select("*").eq("id", org_id).execute()
    
    if not org_res.data:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return org_res.data[0]


@router.get("/members")
async def get_organization_members(
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """List all team members in the user's organization."""
    user_db = supabase.table("users").select("organization_id, role").eq("id", user.id).execute()
    org_id = user_db.data[0]["organization_id"]
    
    members = supabase.table("users").select("id, email, full_name, role, created_at").eq("organization_id", org_id).execute()
    return members.data
