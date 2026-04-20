from fastapi import HTTPException, Header, Depends
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


def get_current_user_with_org(
    user=Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Return the authenticated user augmented with organization_id and role.

    Every downstream route that operates on organization-scoped data should
    depend on this instead of get_current_user so that we have a single
    authoritative source for org_id and role — eliminating per-route lookups
    and closing cross-org data-leak holes.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    row = supabase.table("users").select("organization_id, role, email").eq("id", user.id).execute()
    if not row.data:
        raise HTTPException(status_code=403, detail="User profile not found")

    profile = row.data[0]
    org_id = profile.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="User is not linked to an organization")

    return {
        "id": user.id,
        "email": profile.get("email") or user.email,
        "organization_id": org_id,
        "role": profile.get("role") or "Member",
    }


OWNER_ROLES = {"Owner", "Admin"}


def require_owner(ctx: dict = Depends(get_current_user_with_org)) -> dict:
    if ctx.get("role") not in OWNER_ROLES:
        raise HTTPException(status_code=403, detail="Requires Owner or Admin role")
    return ctx
