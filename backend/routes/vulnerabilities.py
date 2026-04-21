from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import List, Optional

from backend.dependencies import get_supabase, get_current_user_with_org
from backend.models_pydantic import VulnerabilityOut


router = APIRouter(prefix="/vulnerabilities", tags=["Vulnerabilities"])


def _split_csv(raw: str | None) -> list[str]:
    return [s.strip() for s in (raw or "").split(",") if s.strip()]


def _org_scope(org_id: str, supabase: Client) -> tuple[list[str], list[str], bool]:
    """Return (enabled_oems, scanned_oems, has_scanned).

    CVE rows live in a single shared pool (one row per CVE, not per-tenant).
    To decide what this org can see we combine two signals:

    * ``enabled_oems``  -- the vendors they subscribed to at checkout. Empty /
      "ALL" means unrestricted subscription.
    * ``scanned_oems``  -- the vendors THIS org has actually pulled data for
      (manual or scheduled). Without this scoping, the moment a brand-new org
      scans Adobe they'd also see every Cisco / Microsoft / etc. CVE that any
      other tenant's scan had already populated — which is exactly what
      surfaced during demo testing.

    Callers treat ``has_scanned`` as the "show empty state" flag and
    ``scanned_oems`` as the concrete filter.
    """
    org = supabase.table("organizations").select(
        "enabled_oems, scanned_oems, last_scan_at"
    ).eq("id", org_id).execute()
    if not org.data:
        return [], [], False
    row = org.data[0]
    raw_enabled = (row.get("enabled_oems") or "").strip()
    enabled = [] if not raw_enabled or raw_enabled.upper() == "ALL" else _split_csv(raw_enabled)
    scanned = _split_csv(row.get("scanned_oems"))
    has_scanned = bool(row.get("last_scan_at")) and bool(scanned)
    return enabled, scanned, has_scanned


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

    enabled_oems, scanned_oems, has_scanned = _org_scope(
        ctx["organization_id"], supabase
    )
    if not has_scanned:
        return []

    # Intersect scanned with subscribed — scanned should already be a subset,
    # but if the subscription was narrowed after a scan, respect the current
    # subscription as the outer bound.
    visible = scanned_oems
    if enabled_oems:
        visible = [o for o in scanned_oems if o in enabled_oems]
    if not visible:
        return []
    if oem and oem not in visible:
        return []

    query = supabase.table("vulnerabilities").select("*").in_(
        "oem_name", [oem] if oem else visible
    )
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
    enabled_oems, scanned_oems, has_scanned = _org_scope(
        ctx["organization_id"], supabase
    )
    if not has_scanned:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    if vuln.get("oem_name") not in scanned_oems:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    if enabled_oems and vuln.get("oem_name") not in enabled_oems:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln
