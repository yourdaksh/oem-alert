"""
Cron entrypoint for Render's Cron Job service.

Why this is a standalone script instead of an API call:
the API runs on a 512MB Starter instance, and loading 24 scrapers in-process
(BeautifulSoup + selenium imports + ~1000 parsed CVE records) reliably OOMs
the container. Running here means scraping happens in its own short-lived
container that exits when done, freeing the memory.

Invoked hourly. Decides whether to run based on:
1. Any org with `manual_scan_requested_at IS NOT NULL` — Run-Now button press.
2. Any org whose last_scan_at + scan_interval_hours <= now.

If at least one org matches, runs every enabled scraper once (the vulnerability
pool is shared across tenants), then stamps last_scan_at on the triggering orgs
and clears manual_scan_requested_at.
"""
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from supabase import create_client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("scheduled_scrapers")


def _supabase():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def _orgs_needing_scan(sb) -> list[str]:
    """Return ids of orgs due for a scan (interval elapsed or manual trigger)."""
    rows = sb.table("organizations").select(
        "id, scan_interval_hours, last_scan_at, manual_scan_requested_at"
    ).execute().data or []

    now = datetime.now(timezone.utc)
    due: list[str] = []
    for o in rows:
        if o.get("manual_scan_requested_at"):
            due.append(o["id"])
            continue
        interval_h = int(o.get("scan_interval_hours") or 6)
        last = o.get("last_scan_at")
        if not last:
            due.append(o["id"])
            continue
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except Exception:
            due.append(o["id"])
            continue
        if now - last_dt >= timedelta(hours=interval_h):
            due.append(o["id"])
    return due


def _run_all_scrapers() -> dict:
    """Actually invoke the scraper manager. Heavy imports happen here so the
    top-level script stays cheap when the run is a no-op."""
    from run_scrapers import run_scrapers
    return run_scrapers()


def main() -> int:
    sb = _supabase()
    due = _orgs_needing_scan(sb)

    if not due:
        logger.info("no orgs due for scan; exiting")
        return 0

    logger.info("scanning for %d orgs", len(due))
    try:
        summary = _run_all_scrapers()
        logger.info("scrape summary: %s", summary)
    except Exception:
        logger.exception("scrape failed")
        # Still clear manual requests so they don't retry forever on a broken build.
        sb.table("organizations").update({
            "manual_scan_requested_at": None,
        }).in_("id", due).execute()
        return 1

    now_iso = datetime.now(timezone.utc).isoformat()
    sb.table("organizations").update({
        "last_scan_at": now_iso,
        "manual_scan_requested_at": None,
    }).in_("id", due).execute()
    logger.info("stamped last_scan_at for %d orgs", len(due))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
