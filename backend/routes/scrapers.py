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
    """Queue a scan for the caller's org — cron picks it up within 5 min."""
    sb = get_supabase()
    sb.table("organizations").update({
        "manual_scan_requested_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", ctx["organization_id"]).execute()
    return {
        "status": "queued",
        "message": "Scan queued. Scrapers run on the background scheduler within ~5 minutes.",
    }


@router.post("/run-one/{oem}")
async def run_single_oem(oem: str, ctx: dict = Depends(require_owner)):
    """Synchronous per-OEM scrape for the Manual Scan page.

    Running ONE scraper at a time stays safely under the 512MB API limit,
    and keeping it synchronous means the caller sees `found`/`new` counts
    immediately in the UI. Heavy OEMs (android, apple) are worth keeping
    an eye on — if they OOM we'll move them to cron-only.
    """
    from config import get_all_oems
    valid = set(get_all_oems().keys())
    if oem not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown OEM '{oem}'")
    try:
        from run_scrapers import run_single_oem_scraper
        result = run_single_oem_scraper(oem) or {}
    except Exception as e:
        logger.exception("run-one %s failed", oem)
        raise HTTPException(status_code=500, detail=f"Scraper crashed: {e}")
    finally:
        gc.collect()

    now_iso = datetime.now(timezone.utc).isoformat()
    get_supabase().table("organizations").update({"last_scan_at": now_iso}).eq(
        "id", ctx["organization_id"]
    ).execute()

    return {
        "status": "ok",
        "oem": oem,
        "found": result.get("vulnerabilities_found", 0),
        "new": result.get("new_vulnerabilities", 0),
    }


@router.get("/oems")
async def list_oems(ctx: dict = Depends(require_owner)):
    """Scanner catalog surfaced to the Manual Scan page so buttons are generated dynamically."""
    from config import get_all_oems
    out = []
    for oem_id, conf in get_all_oems().items():
        out.append({
            "id": oem_id,
            "name": conf.get("name") or oem_id,
            "description": conf.get("description") or "",
            "enabled": bool(conf.get("enabled", True)),
        })
    return sorted(out, key=lambda x: x["name"].lower())


@router.get("/status")
async def scan_status(ctx: dict = Depends(require_owner), limit: int = 20):
    sb = get_supabase()
    res = sb.table("scan_logs").select(
        "oem_name, scan_type, status, vulnerabilities_found, new_vulnerabilities, error_message, scan_date"
    ).order("scan_date", desc=True).limit(limit).execute()
    return res.data


@router.head("/tick")
async def tick_head(key: Optional[str] = None):
    """HEAD responder so UptimeRobot's default probe type gets a 200.

    If the monitor stays on HEAD it never runs scrapers — it just confirms
    the endpoint is reachable. Users need to switch their monitor's HTTP
    method to GET for scraping to actually fire.
    """
    expected = os.environ.get("TICK_KEY")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Invalid tick key")
    return {"status": "alive"}


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
