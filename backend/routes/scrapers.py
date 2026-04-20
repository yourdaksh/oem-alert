from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional

from backend.dependencies import require_owner


router = APIRouter(prefix="/scrapers", tags=["Scrapers"])


def _run_job(oem: Optional[str]):
    """Fire-and-forget scraper invocation executed as a FastAPI BackgroundTask.

    Kept in a helper so the route can return immediately — individual scrapers
    can take minutes when they walk a vendor's advisory pages.
    """
    try:
        from run_scrapers import run_scrapers, run_single_oem_scraper
        if oem:
            return run_single_oem_scraper(oem)
        return run_scrapers()
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("scraper job failed: %s", e)


@router.post("/run")
async def trigger_scrapers(
    background: BackgroundTasks,
    oem: Optional[str] = None,
    ctx: dict = Depends(require_owner),
):
    """Owner-only manual trigger. Runs async so the caller doesn't wait."""
    background.add_task(_run_job, oem)
    return {"status": "queued", "oem": oem or "all"}


@router.get("/status")
async def scan_status(ctx: dict = Depends(require_owner), limit: int = 20):
    """Recent scan logs so operators can see what ran + any failures."""
    from backend.dependencies import get_supabase
    sb = get_supabase()
    res = sb.table("scan_logs").select(
        "oem_name, scan_type, status, vulnerabilities_found, new_vulnerabilities, error_message, scan_date"
    ).order("scan_date", desc=True).limit(limit).execute()
    return res.data
