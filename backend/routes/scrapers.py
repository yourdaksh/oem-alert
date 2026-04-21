import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from backend.dependencies import require_owner, get_supabase


router = APIRouter(prefix="/scrapers", tags=["Scrapers"])
logger = logging.getLogger(__name__)


def _mark_scanned(org_ids: list[str]) -> None:
    """Stamp organizations.last_scan_at after a successful run.

    Done in one UPDATE so a single timestamp applies to the whole batch —
    users see a coherent "last scanned" value instead of staggered writes
    that would happen if we updated per-org.
    """
    if not org_ids:
        return
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    sb.table("organizations").update({"last_scan_at": now}).in_("id", org_ids).execute()


def _run_all(org_ids: Optional[list[str]] = None, oem: Optional[str] = None) -> None:
    """Background-task body that actually drives the scrapers.

    Kept outside the handler so BackgroundTasks serialization doesn't capture
    request state; also lets the Render cron wrapper call it directly.
    """
    try:
        from run_scrapers import run_scrapers, run_single_oem_scraper
        result = run_single_oem_scraper(oem) if oem else run_scrapers()
        logger.info("scrape done: %s", result)
        _mark_scanned(org_ids or [])
    except Exception:
        logger.exception("scrape job failed")


@router.post("/run")
async def trigger_scrapers(
    background: BackgroundTasks,
    oem: Optional[str] = None,
    ctx: dict = Depends(require_owner),
):
    """Owner-triggered manual scrape. Runs async so the client returns quickly."""
    background.add_task(_run_all, [ctx["organization_id"]], oem)
    return {"status": "queued", "oem": oem or "all"}


@router.get("/status")
async def scan_status(ctx: dict = Depends(require_owner), limit: int = 20):
    sb = get_supabase()
    res = sb.table("scan_logs").select(
        "oem_name, scan_type, status, vulnerabilities_found, new_vulnerabilities, error_message, scan_date"
    ).order("scan_date", desc=True).limit(limit).execute()
    return res.data


@router.post("/run-due")
async def run_due_scrapers(
    background: BackgroundTasks,
    x_cron_key: str | None = Header(default=None, alias="X-Cron-Key"),
):
    """Shared-secret endpoint meant to be hit by Render Cron every hour.

    Pulls organizations whose last_scan_at is older than their configured
    scan_interval_hours and fires a single global scrape — cheaper than
    running per-org since vulnerabilities are a shared pool.
    """
    expected = os.environ.get("CRON_SECRET")
    if not expected or x_cron_key != expected:
        raise HTTPException(status_code=401, detail="Invalid cron key")

    sb = get_supabase()
    orgs = sb.table("organizations").select(
        "id, scan_interval_hours, last_scan_at"
    ).execute().data or []

    now = datetime.now(timezone.utc)
    due_ids: list[str] = []
    for o in orgs:
        interval_h = int(o.get("scan_interval_hours") or 6)
        last = o.get("last_scan_at")
        if not last:
            due_ids.append(o["id"])
            continue
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except Exception:
            due_ids.append(o["id"])
            continue
        if now - last_dt >= timedelta(hours=interval_h):
            due_ids.append(o["id"])

    if not due_ids:
        return {"status": "skipped", "reason": "no orgs due", "checked": len(orgs)}

    background.add_task(_run_all, due_ids, None)
    return {"status": "queued", "orgs_due": len(due_ids), "total_orgs": len(orgs)}
