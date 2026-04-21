from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import Client
from datetime import datetime, timedelta, timezone
import secrets

from backend.dependencies import (
    get_supabase,
    get_current_user_with_org,
    require_owner,
)


router = APIRouter(prefix="/organizations", tags=["Organizations"])


VALID_ROLES = {"Owner", "Admin", "Analyst", "Viewer"}


@router.get("/me")
async def get_my_organization(
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    org_res = supabase.table("organizations").select("*").eq(
        "id", ctx["organization_id"]
    ).execute()
    if not org_res.data:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_res.data[0]


VALID_INTERVALS = {1, 3, 6, 12, 24, 48, 168}


VALID_ALERT_SEVERITIES = {"Critical", "High", "Medium", "Low"}


class OrgSettingsUpdate(BaseModel):
    scan_interval_hours: int | None = None
    enabled_oems: str | None = None
    alert_email: str | None = None
    slack_webhook_url: str | None = None
    alerts_enabled: bool | None = None
    alert_min_severity: str | None = None


@router.patch("/settings")
async def update_org_settings(
    req: OrgSettingsUpdate,
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    """Owner-only update for org-level preferences the product surfaces.

    Intervals are constrained to a whitelist so the UI can pick from a dropdown
    and we don't end up with one-off weird values that skew the global cron."""
    patch: dict = {}
    if req.scan_interval_hours is not None:
        if req.scan_interval_hours not in VALID_INTERVALS:
            raise HTTPException(
                status_code=400,
                detail=f"scan_interval_hours must be one of {sorted(VALID_INTERVALS)}",
            )
        patch["scan_interval_hours"] = req.scan_interval_hours
    if req.enabled_oems is not None:
        patch["enabled_oems"] = req.enabled_oems
    if req.alert_email is not None:
        patch["alert_email"] = req.alert_email.strip() or None
    if req.slack_webhook_url is not None:
        url = (req.slack_webhook_url or "").strip() or None
        if url and not url.startswith("https://hooks.slack.com/"):
            raise HTTPException(status_code=400, detail="slack_webhook_url must start with https://hooks.slack.com/")
        patch["slack_webhook_url"] = url
    if req.alerts_enabled is not None:
        patch["alerts_enabled"] = bool(req.alerts_enabled)
    if req.alert_min_severity is not None:
        sev = req.alert_min_severity.capitalize()
        if sev not in VALID_ALERT_SEVERITIES:
            raise HTTPException(status_code=400, detail=f"alert_min_severity must be one of {sorted(VALID_ALERT_SEVERITIES)}")
        patch["alert_min_severity"] = sev
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")

    supabase.table("organizations").update(patch).eq(
        "id", ctx["organization_id"]
    ).execute()
    updated = supabase.table("organizations").select("*").eq(
        "id", ctx["organization_id"]
    ).execute()
    return updated.data[0]


@router.post("/alerts/test")
async def test_alerts(
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    """Send a sample digest with the org's current config so Owners can verify
    email/slack work before relying on real CVE alerts."""
    from utils.alerts import Org, _parse_oems, send_email, send_slack
    r = supabase.table("organizations").select(
        "id, name, enabled_oems, alert_email, slack_webhook_url, alerts_enabled, alert_min_severity"
    ).eq("id", ctx["organization_id"]).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Organization not found")
    o = r.data[0]
    org = Org(
        id=o["id"],
        name=o.get("name") or "Your Organization",
        enabled_oems=_parse_oems(o.get("enabled_oems")),
        alert_email=o.get("alert_email"),
        slack_webhook_url=o.get("slack_webhook_url"),
        alerts_enabled=bool(o.get("alerts_enabled", True)),
        alert_min_severity=o.get("alert_min_severity") or "High",
    )
    sample = [{
        "unique_id": "CVE-SAMPLE-0001",
        "oem_name": "Example",
        "severity_level": org.alert_min_severity,
        "vulnerability_description": "This is a sample alert confirming your OEM Alert email/Slack wiring is live.",
        "source_url": "https://example.com",
    }]
    email_ok = send_email(org, sample) if org.alert_email else None
    slack_ok = send_slack(org, sample) if org.slack_webhook_url else None
    return {"email": email_ok, "slack": slack_ok}


@router.get("/members")
async def get_organization_members(
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    members = supabase.table("users").select(
        "id, email, full_name, role, created_at"
    ).eq("organization_id", ctx["organization_id"]).execute()
    return members.data


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "Analyst"


@router.post("/invite")
async def create_invite(
    req: InviteRequest,
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    """Create an invitation scoped to the caller's organization.

    Returns the full invite URL so the caller can share it manually while email
    is still being wired up. Refusing to issue invites for members already in
    the org avoids dead-end links.
    """
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {sorted(VALID_ROLES)}")
    if req.role == "Owner":
        raise HTTPException(status_code=400, detail="Cannot invite another Owner")

    existing_user = supabase.table("users").select("id").eq(
        "email", req.email
    ).eq("organization_id", ctx["organization_id"]).execute()
    if existing_user.data:
        raise HTTPException(status_code=409, detail="User is already a member")

    existing_invite = supabase.table("invitations").select("id").eq(
        "email", req.email
    ).eq("organization_id", ctx["organization_id"]).eq("status", "Pending").execute()
    if existing_invite.data:
        raise HTTPException(status_code=409, detail="Pending invitation already exists for this email")

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    res = supabase.table("invitations").insert({
        "email": req.email,
        "organization_id": ctx["organization_id"],
        "role": req.role,
        "token": token,
        "status": "Pending",
        "invited_by": ctx["id"],
        "expires_at": expires_at,
    }).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create invitation")

    import os
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return {
        "id": res.data[0]["id"],
        "token": token,
        "invite_url": f"{frontend_url}/invite/{token}",
        "email": req.email,
        "role": req.role,
        "expires_at": expires_at,
    }


@router.get("/invitations")
async def list_invitations(
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    res = supabase.table("invitations").select(
        "id, email, role, status, expires_at, created_at, invited_by, token"
    ).eq("organization_id", ctx["organization_id"]).order(
        "created_at", desc=True
    ).execute()
    return res.data


@router.delete("/invitations/{invite_id}")
async def revoke_invitation(
    invite_id: str,
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    target = supabase.table("invitations").select("organization_id").eq(
        "id", invite_id
    ).execute()
    if not target.data:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if target.data[0]["organization_id"] != ctx["organization_id"]:
        raise HTTPException(status_code=403, detail="Cannot revoke invites from another organization")

    supabase.table("invitations").update({"status": "Revoked"}).eq(
        "id", invite_id
    ).execute()
    return {"status": "revoked"}


class RoleUpdateRequest(BaseModel):
    role: str


@router.patch("/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    req: RoleUpdateRequest,
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {sorted(VALID_ROLES)}")

    target = supabase.table("users").select("organization_id, role").eq(
        "id", user_id
    ).execute()
    if not target.data:
        raise HTTPException(status_code=404, detail="User not found")
    if target.data[0]["organization_id"] != ctx["organization_id"]:
        raise HTTPException(status_code=403, detail="Cannot modify users in another organization")
    if target.data[0]["role"] == "Owner" and req.role != "Owner":
        raise HTTPException(status_code=400, detail="Cannot demote the Owner; transfer ownership first")

    supabase.table("users").update({"role": req.role}).eq("id", user_id).execute()
    return {"status": "updated", "role": req.role}


@router.delete("/members/{user_id}")
async def remove_member(
    user_id: str,
    ctx: dict = Depends(require_owner),
    supabase: Client = Depends(get_supabase),
):
    if user_id == ctx["id"]:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    target = supabase.table("users").select("organization_id, role").eq(
        "id", user_id
    ).execute()
    if not target.data:
        raise HTTPException(status_code=404, detail="User not found")
    if target.data[0]["organization_id"] != ctx["organization_id"]:
        raise HTTPException(status_code=403, detail="Cannot remove users from another organization")
    if target.data[0]["role"] == "Owner":
        raise HTTPException(status_code=400, detail="Cannot remove an Owner")

    supabase.table("users").update({"organization_id": None, "role": "Member"}).eq(
        "id", user_id
    ).execute()
    return {"status": "removed"}
