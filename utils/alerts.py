"""
Org-level digest alerts — email + Slack.

Decoupled from the old per-user Subscription-based email module so we can wire
it directly to the scraper pipeline. After a scrape completes, for every org
with alerts enabled, collect the newly-inserted vulnerabilities affecting their
enabled OEMs at their min-severity threshold and send a single digest out.

Keeping the plumbing here (outside backend/) means the cron script can import
and run it without dragging FastAPI into the cron container.
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Iterable

import requests


logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Moderate": 2, "Low": 1, "Unknown": 0}


@dataclass
class Org:
    id: str
    name: str
    enabled_oems: list[str]
    alert_email: str | None
    slack_webhook_url: str | None
    alerts_enabled: bool
    alert_min_severity: str


def _meets_severity(severity: str | None, threshold: str) -> bool:
    s = SEVERITY_ORDER.get((severity or "").capitalize(), 0)
    t = SEVERITY_ORDER.get((threshold or "High").capitalize(), 3)
    return s >= t


def _render_email_html(org: Org, vulns: list[dict]) -> str:
    rows_html = []
    for v in vulns:
        sev = (v.get("severity_level") or "Unknown").capitalize()
        color = {"Critical": "#dc3545", "High": "#fd7e14", "Medium": "#f59e0b", "Low": "#10b981"}.get(sev, "#6b7280")
        rows_html.append(f"""
          <tr style="border-bottom:1px solid #e5e7eb">
            <td style="padding:10px 12px"><span style="background:{color}22;color:{color};padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700">{sev.upper()}</span></td>
            <td style="padding:10px 12px;font-family:ui-monospace,Menlo,monospace;font-size:12px">{v.get("unique_id","")}</td>
            <td style="padding:10px 12px;font-size:13px">{v.get("oem_name","")}</td>
            <td style="padding:10px 12px;font-size:13px;color:#374151">{(v.get("vulnerability_description") or "")[:200]}</td>
          </tr>""")
    return f"""\
<!doctype html>
<html><body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,sans-serif">
  <div style="max-width:680px;margin:0 auto;padding:24px">
    <h1 style="font-size:20px;margin:0 0 4px 0;color:#111">OEM Alert digest — {org.name}</h1>
    <p style="color:#6b7280;font-size:13px;margin:0 0 20px 0">{len(vulns)} new vulnerability findings at or above <b>{org.alert_min_severity}</b></p>
    <table style="width:100%;border-collapse:collapse;background:white;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
      <thead style="background:#f3f4f6">
        <tr>
          <th style="text-align:left;padding:10px 12px;font-size:11px;text-transform:uppercase;color:#6b7280;letter-spacing:0.5px">Severity</th>
          <th style="text-align:left;padding:10px 12px;font-size:11px;text-transform:uppercase;color:#6b7280;letter-spacing:0.5px">CVE</th>
          <th style="text-align:left;padding:10px 12px;font-size:11px;text-transform:uppercase;color:#6b7280;letter-spacing:0.5px">OEM</th>
          <th style="text-align:left;padding:10px 12px;font-size:11px;text-transform:uppercase;color:#6b7280;letter-spacing:0.5px">Summary</th>
        </tr>
      </thead>
      <tbody>{''.join(rows_html)}</tbody>
    </table>
    <p style="color:#9ca3af;font-size:12px;margin-top:20px">Sent by OEM Alert. Change your alert settings in the dashboard.</p>
  </div>
</body></html>"""


def send_email(org: Org, vulns: list[dict]) -> bool:
    if not org.alert_email or not vulns:
        return False
    host = os.environ.get("SMTP_SERVER")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("EMAIL_USERNAME")
    password = os.environ.get("EMAIL_PASSWORD")
    from_addr = os.environ.get("FROM_EMAIL") or user
    if not (host and user and password and from_addr):
        logger.info("SMTP not configured — skipping email to %s", org.alert_email)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[OEM Alert] {len(vulns)} new {org.alert_min_severity.lower()}+ vulnerabilities"
        msg["From"] = from_addr
        msg["To"] = org.alert_email
        msg.attach(MIMEText(_render_email_html(org, vulns), "html"))
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls()
            s.login(user, password)
            s.sendmail(from_addr, [org.alert_email], msg.as_string())
        logger.info("email digest sent to %s (%d rows)", org.alert_email, len(vulns))
        return True
    except Exception as e:
        logger.error("email send failed for %s: %s", org.alert_email, e)
        return False


def send_slack(org: Org, vulns: list[dict]) -> bool:
    if not org.slack_webhook_url or not vulns:
        return False
    sev_emoji = {"Critical": ":rotating_light:", "High": ":warning:", "Medium": ":large_yellow_circle:", "Low": ":white_check_mark:"}
    lines = [f"*{len(vulns)} new vulnerabilities* for `{org.name}` (threshold: *{org.alert_min_severity}*)"]
    for v in vulns[:20]:  # cap so Slack doesn't reject the payload
        sev = (v.get("severity_level") or "Unknown").capitalize()
        emoji = sev_emoji.get(sev, ":grey_question:")
        line = f"{emoji} *{sev}* — `{v.get('unique_id','')}` — {v.get('oem_name','')} — {(v.get('vulnerability_description') or '')[:140]}"
        if v.get("source_url"):
            line += f" <{v['source_url']}|source>"
        lines.append(line)
    if len(vulns) > 20:
        lines.append(f"_… and {len(vulns) - 20} more_")
    try:
        r = requests.post(org.slack_webhook_url, json={"text": "\n".join(lines)}, timeout=10)
        r.raise_for_status()
        logger.info("slack digest sent for %s (%d rows)", org.name, len(vulns))
        return True
    except Exception as e:
        logger.error("slack send failed for %s: %s", org.name, e)
        return False


def _parse_oems(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


_FIRST_SCAN_DIGEST_CAP = 50


def notify_single_org(
    supabase,
    org_id: str,
    since: datetime,
    *,
    scoped_oem: str | None = None,
    include_existing: bool = False,
) -> dict:
    """Run the digest send for exactly one org — used by the manual-scan path.

    The scheduled cron uses ``notify_orgs_of_new_vulns`` to fan out across every
    tenant at once. A manual scan is scoped to the triggering org, so we skip
    the scan across the whole org table and only touch the one we care about.

    ``include_existing=True`` widens the query from "inserted since T" to
    "every currently-visible CVE in the scoped OEMs at or above the threshold".
    This is the right behavior the first time an org scans a given OEM: the
    CVE pool is shared, so Adobe's advisories were probably already inserted
    by another tenant's cron — narrowing to ``created_at >= since`` would
    return zero and the owner never gets a welcome digest for that vendor.

    ``scoped_oem`` narrows the digest to a single OEM (display name), used
    when the manual-scan path runs one OEM at a time so the user sees the
    email clearly attributed to the scan they just triggered.
    """
    rows = supabase.table("organizations").select(
        "id, name, enabled_oems, scanned_oems, alert_email, slack_webhook_url, "
        "alerts_enabled, alert_min_severity"
    ).eq("id", org_id).execute().data or []
    if not rows:
        return {"sent": False, "reason": "org_not_found"}
    r = rows[0]
    if not r.get("alerts_enabled"):
        return {"sent": False, "reason": "alerts_disabled"}

    org = Org(
        id=r["id"],
        name=r.get("name") or "Your Organization",
        enabled_oems=_parse_oems(r.get("enabled_oems")),
        alert_email=r.get("alert_email"),
        slack_webhook_url=r.get("slack_webhook_url"),
        alerts_enabled=True,
        alert_min_severity=r.get("alert_min_severity") or "High",
    )
    if not org.alert_email and not org.slack_webhook_url:
        return {"sent": False, "reason": "no_destination"}

    scanned = _parse_oems(r.get("scanned_oems"))
    allowed_oems = [o for o in scanned if not org.enabled_oems or o in org.enabled_oems]
    if scoped_oem and scoped_oem in allowed_oems:
        allowed_oems = [scoped_oem]
    if not allowed_oems:
        return {"sent": False, "reason": "no_oems_in_scope"}

    query = supabase.table("vulnerabilities").select(
        "id, unique_id, oem_name, severity_level, vulnerability_description, source_url, created_at, published_date"
    ).in_("oem_name", allowed_oems)
    if not include_existing:
        query = query.gte("created_at", since.isoformat())
    # Order newest-first and cap; keeps the email digest to a readable length
    # even on a first-time scan of a noisy vendor like Android or Microsoft.
    query = query.order("published_date", desc=True).limit(_FIRST_SCAN_DIGEST_CAP * 4)

    vulns = query.execute().data or []

    relevant = [
        v for v in vulns
        if _meets_severity(v.get("severity_level"), org.alert_min_severity)
    ][:_FIRST_SCAN_DIGEST_CAP]

    if not relevant:
        return {"sent": False, "reason": "no_matching_vulns", "candidates": len(vulns)}

    email_ok = send_email(org, relevant) if org.alert_email else None
    slack_ok = send_slack(org, relevant) if org.slack_webhook_url else None
    return {
        "sent": bool(email_ok or slack_ok),
        "email": email_ok,
        "slack": slack_ok,
        "count": len(relevant),
        "mode": "full_digest" if include_existing else "delta",
    }


def notify_orgs_of_new_vulns(supabase, since: datetime | None = None) -> dict:
    """Send digests to every org whose alerts are enabled.

    `since` bounds what counts as "new" — default: last 2 hours, which covers
    the typical cron interval. Idempotent-ish: if you call it twice quickly
    you'll send two digests, so callers should pass a real cutoff.
    """
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(hours=2)

    orgs_rows = supabase.table("organizations").select(
        "id, name, enabled_oems, scanned_oems, alert_email, slack_webhook_url, alerts_enabled, alert_min_severity"
    ).eq("alerts_enabled", True).execute().data or []

    if not orgs_rows:
        return {"orgs_notified": 0, "emails_sent": 0, "slacks_sent": 0}

    vulns = supabase.table("vulnerabilities").select(
        "id, unique_id, oem_name, severity_level, vulnerability_description, source_url, created_at"
    ).gte("created_at", since.isoformat()).execute().data or []

    emails = slacks = notified = 0
    for r in orgs_rows:
        org = Org(
            id=r["id"],
            name=r.get("name") or "Your Organization",
            enabled_oems=_parse_oems(r.get("enabled_oems")),
            alert_email=r.get("alert_email"),
            slack_webhook_url=r.get("slack_webhook_url"),
            alerts_enabled=bool(r.get("alerts_enabled", True)),
            alert_min_severity=r.get("alert_min_severity") or "High",
        )
        if not org.alert_email and not org.slack_webhook_url:
            continue
        scanned = _parse_oems(r.get("scanned_oems"))
        relevant = [
            v for v in vulns
            if (not scanned or v.get("oem_name") in scanned)
            and (not org.enabled_oems or v.get("oem_name") in org.enabled_oems)
            and _meets_severity(v.get("severity_level"), org.alert_min_severity)
        ]
        if not relevant:
            continue
        if send_email(org, relevant):
            emails += 1
        if send_slack(org, relevant):
            slacks += 1
        if emails or slacks:
            notified += 1
    return {"orgs_notified": notified, "emails_sent": emails, "slacks_sent": slacks}
