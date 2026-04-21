import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_owner, get_supabase


router = APIRouter(prefix="/scrapers", tags=["Scrapers"])
logger = logging.getLogger(__name__)


@router.post("/run")
async def request_manual_scan(ctx: dict = Depends(require_owner)):
    """Queue a manual scan for the caller's org.

    We do NOT run scrapers in the API process: the 512MB API instance OOMs
    when 24 scrapers load BeautifulSoup + ~1000 parsed records. Instead we
    set `manual_scan_requested_at` on the org; the hourly cron picks it up
    and runs the scrape in its own short-lived container.
    """
    sb = get_supabase()
    sb.table("organizations").update({
        "manual_scan_requested_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", ctx["organization_id"]).execute()
    return {
        "status": "queued",
        "message": "Scan queued. Will run within the next hour on the scheduled cron.",
    }


@router.get("/status")
async def scan_status(ctx: dict = Depends(require_owner), limit: int = 20):
    sb = get_supabase()
    res = sb.table("scan_logs").select(
        "oem_name, scan_type, status, vulnerabilities_found, new_vulnerabilities, error_message, scan_date"
    ).order("scan_date", desc=True).limit(limit).execute()
    return res.data
