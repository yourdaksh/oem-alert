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
import re
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


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MRKDWN_UNSAFE_RE = re.compile(r"[<>&]")
_MRKDWN_ESCAPES = {"<": "&lt;", ">": "&gt;", "&": "&amp;"}


def _slack_escape(raw: str) -> str:
    """Prep a string for Slack's mrkdwn `text` field.

    Slack treats ``<`` as the start of a link token (``<url|display>``) and
    returns a 400 if it can't match one, which is the most common reason a
    webhook that worked for the canned Send-test payload fails on real CVE
    descriptions (vendors embed raw HTML: ``<p>``, ``<br>``, etc.). Strip
    HTML tags first, then escape the three mrkdwn-special characters that
    remain. Also collapse whitespace so newlines in source don't break lines.
    """
    if not raw:
        return ""
    cleaned = _HTML_TAG_RE.sub(" ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return _MRKDWN_UNSAFE_RE.sub(lambda m: _MRKDWN_ESCAPES[m.group(0)], cleaned)


def send_slack_detailed(org: Org, vulns: list[dict]) -> tuple[bool, str | None]:
    """Post the digest to the Slack webhook and return (ok, error_message).

    Slack's ``text``-payload cap is ~4000 characters; longer bodies 400 with
    ``invalid_payload``. We cap at 10 rows with short descriptions (~120
    chars) so the total message stays comfortably under the limit even with
    emoji and URL escape sequences. Anything over 10 gets summarised as
    ``… and N more`` so the digest still conveys volume.
    """
    if not org.slack_webhook_url:
        return False, "no_webhook_configured"
    if not vulns:
        return False, "empty_digest"

    sev_emoji = {
        "Critical": ":rotating_light:",
        "High": ":warning:",
        "Medium": ":large_yellow_circle:",
        "Low": ":white_check_mark:",
    }

    org_name = _slack_escape(org.name or "Your Organization")
    threshold = _slack_escape(org.alert_min_severity or "High")
    lines = [f"*{len(vulns)} vulnerability findings* for `{org_name}` (threshold: *{threshold}*)"]

    MAX_ROWS = 10
    DESC_LEN = 120
    for v in vulns[:MAX_ROWS]:
        sev = (v.get("severity_level") or "Unknown").capitalize()
        emoji = sev_emoji.get(sev, ":grey_question:")
        cve = _slack_escape(v.get("unique_id") or "")
        oem = _slack_escape(v.get("oem_name") or "")
        desc = _slack_escape(v.get("vulnerability_description") or "")[:DESC_LEN]
        line = f"{emoji} *{sev}* `{cve}` — {oem}"
        if desc:
            line += f" — {desc}"
        # Only inline a source link if it parses as an https URL — stops
        # vendor "javascript:" or relative junk from blowing up the payload.
        src = v.get("source_url") or ""
        if isinstance(src, str) and src.startswith(("http://", "https://")):
            # Slack link syntax <url|label>; the URL itself must not contain
            # unescaped |> characters.
            safe_url = src.replace("|", "%7C").replace(">", "%3E")
            line += f" <{safe_url}|source>"
        lines.append(line)

    if len(vulns) > MAX_ROWS:
        lines.append(f"_… and {len(vulns) - MAX_ROWS} more_")

    payload = {"text": "\n".join(lines)}
    try:
        r = requests.post(org.slack_webhook_url, json=payload, timeout=10)
    except requests.Timeout:
        logger.error("slack send timed out for %s", org.name)
        return False, "timeout_contacting_slack"
    except Exception as e:
        logger.error("slack send raised for %s: %s", org.name, e)
        return False, f"network_error: {e}"[:180]

    if 200 <= r.status_code < 300:
        logger.info("slack digest sent for %s (%d rows)", org.name, len(vulns))
        return True, None

    body = (r.text or "")[:180]
    logger.error("slack webhook %d for %s: %s", r.status_code, org.name, body)
    # Slack returns specific body codes that are worth surfacing to the UI —
    # they point the user straight at the real fix.
    hint_map = {
        "invalid_payload": "payload format rejected (length or special chars)",
        "no_service": "webhook URL is inactive or revoked — regenerate it",
        "channel_is_archived": "target Slack channel is archived",
        "invalid_token": "webhook token is invalid",
        "action_prohibited": "webhook is missing workspace permission",
    }
    hint = hint_map.get(body.strip(), None)
    reason = f"http_{r.status_code}"
    if hint:
        reason += f": {hint}"
    elif body:
        reason += f": {body}"
    return False, reason


def send_slack(org: Org, vulns: list[dict]) -> bool:
    """Back-compat wrapper — most callers only care about the boolean."""
    ok, _ = send_slack_detailed(org, vulns)
    return ok


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
