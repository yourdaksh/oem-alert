import gc
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_owner, get_supabase


router = APIRouter(prefix="/scrapers", tags=["Scrapers"])
logger = logging.getLogger(__name__)


@router.post("/run")
async def request_manual_scan(ctx: dict = Depends(require_owner)):
    """Queue a manual scan for the caller's org — the tick endpoint picks it up.

    We deliberately don't run anything in the API process; the 512MB Starter
    instance OOMs when scrapers load BeautifulSoup + parsed records. The queue
    flag is cleared after the next tick that picks the stalest OEM.
    """
    sb = get_supabase()
    sb.table("organizations").update({
        "manual_scan_requested_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", ctx["organization_id"]).execute()
    return {
        "status": "queued",
        "message": "Scan queued. Scrapers run one-per-tick on the background scheduler.",
    }


@router.get("/status")
async def scan_status(ctx: dict = Depends(require_owner), limit: int = 20):
    sb = get_supabase()
    res = sb.table("scan_logs").select(
        "oem_name, scan_type, status, vulnerabilities_found, new_vulnerabilities, error_message, scan_date"
    ).order("scan_date", desc=True).limit(limit).execute()
    return res.data


@router.get("/tick")
async def tick(key: Optional[str] = None):
    """Single-OEM scrape intended to be hit every 5 minutes by UptimeRobot.

    Running all 23 scrapers in-process OOMs the API. This endpoint picks the
    OEM whose most-recent scan_log row is oldest (or who has never been
    scanned) and runs *only* that one scraper. A full rotation of 23 OEMs on
    a 5-minute ping = one complete refresh every ~2 hours, well under any
    reasonable SLA for CVE freshness.
    """
    expected = os.environ.get("TICK_KEY")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Invalid tick key")

    sb = get_supabase()

    # Lazy import: loading the scraper manager pulls in 20+ modules and BS4.
    # Keeping it inside the handler means the idle API process stays slim.
    from config import get_enabled_oems
    all_oems = [o for o in get_enabled_oems()]

    recent_logs = sb.table("scan_logs").select(
        "oem_name, scan_date"
    ).order("scan_date", desc=True).limit(500).execute().data or []

    latest_scan: dict[str, str] = {}
    for row in recent_logs:
        name = (row.get("oem_name") or "").lower()
        if name and name not in latest_scan:
            latest_scan[name] = row.get("scan_date") or ""

    never = [o for o in all_oems if o not in latest_scan]
    if never:
        target = never[0]
    elif all_oems:
        target = min(all_oems, key=lambda o: latest_scan.get(o, ""))
    else:
        raise HTTPException(status_code=500, detail="No scrapers configured")

    try:
        from run_scrapers import run_single_oem_scraper
        result = run_single_oem_scraper(target)
    except Exception as e:
        logger.exception("tick scrape failed for %s", target)
        return {"status": "error", "oem": target, "error": str(e)[:200]}
    finally:
        gc.collect()

    now_iso = datetime.now(timezone.utc).isoformat()
    sb.table("organizations").update({
        "last_scan_at": now_iso,
        "manual_scan_requested_at": None,
    }).execute()

    return {
        "status": "ok",
        "oem": target,
        "found": (result or {}).get("vulnerabilities_found", 0),
        "new": (result or {}).get("new_vulnerabilities", 0),
    }
