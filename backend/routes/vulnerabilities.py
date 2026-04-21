from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import List, Optional

from backend.dependencies import get_supabase, get_current_user_with_org
from backend.models_pydantic import VulnerabilityOut


router = APIRouter(prefix="/vulnerabilities", tags=["Vulnerabilities"])


def _org_scope(org_id: str, supabase: Client) -> tuple[list[str], bool]:
    """Return (enabled_oems, has_scanned).

    Scraped rows live in a shared pool; we filter at read time so each tenant
    only sees the vendors they subscribed to. On top of that, a freshly-created
    org with no completed scans gets an empty view — showing them the pre-existing
    shared-pool rows would be misleading ("did I scan these?"). They see their
    data only after they've run their first scan.
    Empty/"ALL" enabled_oems means unrestricted once scanning has happened.
    """
    org = supabase.table("organizations").select("enabled_oems, last_scan_at").eq(
        "id", org_id
    ).execute()
    if not org.data:
        return [], False
    row = org.data[0]
    raw = (row.get("enabled_oems") or "").strip()
    oems = [] if not raw or raw.upper() == "ALL" else [o.strip() for o in raw.split(",") if o.strip()]
    has_scanned = bool(row.get("last_scan_at"))
    return oems, has_scanned


@router.get("/", response_model=List[VulnerabilityOut])
async def get_vulnerabilities(
    oem: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, le=5000),
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection missing")

    org_oems, has_scanned = _org_scope(ctx["organization_id"], supabase)
    # Brand-new orgs start empty until they've completed their first scan,
    # otherwise they'd see the full shared pool and think their scan ran magically.
    if not has_scanned:
        return []

    query = supabase.table("vulnerabilities").select("*")
    if org_oems:
        if oem and oem not in org_oems:
            return []
        query = query.in_("oem_name", [oem] if oem else org_oems)
    elif oem:
        query = query.eq("oem_name", oem)
    if severity:
        query = query.eq("severity_level", severity)

    res = query.order("published_date", desc=True).limit(limit).execute()
    return res.data


@router.get("/{vuln_id}", response_model=VulnerabilityOut)
async def get_vulnerability(
    vuln_id: str,
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    res = supabase.table("vulnerabilities").select("*").eq("id", vuln_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    vuln = res.data[0]
    org_oems, has_scanned = _org_scope(ctx["organization_id"], supabase)
    if not has_scanned:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    if org_oems and vuln.get("oem_name") not in org_oems:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln
