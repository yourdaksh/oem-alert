import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.dependencies import get_supabase


logger = logging.getLogger(__name__)


class _VulnRecord:
    """Minimal shape the scraper runner reads back from add_vulnerability."""
    def __init__(self, row: Dict[str, Any]):
        self.unique_id = row.get("unique_id")
        raw = row.get("created_at") or row.get("published_date")
        if isinstance(raw, str):
            try:
                self.discovered_date = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except Exception:
                self.discovered_date = datetime.now()
        elif raw is not None:
            self.discovered_date = raw
        else:
            self.discovered_date = datetime.now()


class SupabaseOperations:
    """Scraper-side Supabase writer.

    Vulnerabilities live in a shared pool (organization_id NULL). The API
    filters per-tenant at read time against each org's enabled_oems list.
    """

    VULN_COLUMNS = (
        "unique_id, product_name, product_version, oem_name, severity_level, "
        "vulnerability_description, mitigation_strategy, published_date, source_url, "
        "cvss_score, affected_versions, created_at"
    )

    def __init__(self):
        self.supabase = get_supabase()
        if not self.supabase:
            logger.error("Supabase client not initialized. SCRAPERS WILL FAIL TO SAVE.")

    def add_vulnerability(self, vuln_data: Dict[str, Any]) -> Optional[_VulnRecord]:
        if not self.supabase:
            return None

        unique_id = vuln_data.get("unique_id")
        if not unique_id:
            logger.warning("skipping row with no unique_id: %r", vuln_data)
            return None

        try:
            existing = self.supabase.table("vulnerabilities").select(
                self.VULN_COLUMNS
            ).eq("unique_id", unique_id).execute()
            if existing.data:
                return _VulnRecord(existing.data[0])

            payload = dict(vuln_data)
            for k, v in list(payload.items()):
                if hasattr(v, "isoformat"):
                    payload[k] = v.isoformat()

            mapped = {
                "unique_id": payload.get("unique_id"),
                "product_name": payload.get("product_name") or payload.get("oem_name"),
                "product_version": payload.get("product_version"),
                "oem_name": payload.get("oem_name"),
                "severity_level": payload.get("severity_level") or "Unknown",
                "vulnerability_description": payload.get("vulnerability_description", ""),
                "mitigation_strategy": payload.get("mitigation_strategy", ""),
                "published_date": payload.get("published_date") or datetime.utcnow().isoformat(),
                "source_url": payload.get("source_url"),
                "cvss_score": str(payload["cvss_score"]) if payload.get("cvss_score") else None,
                "affected_versions": payload.get("affected_versions"),
            }

            result = self.supabase.table("vulnerabilities").insert(mapped).execute()
            if result.data:
                return _VulnRecord(result.data[0])
        except Exception as e:
            logger.error("failed to insert %s: %s", unique_id, e)
            return None

    def log_scan(self, oem_name: str, scan_type: str, status: str,
                 vulnerabilities_found: int = 0, new_vulnerabilities: int = 0,
                 error_message: Optional[str] = None,
                 scan_duration: Optional[int] = None):
        if not self.supabase:
            return
        try:
            self.supabase.table("scan_logs").insert({
                "oem_name": oem_name,
                "scan_type": scan_type,
                "status": status,
                "vulnerabilities_found": vulnerabilities_found,
                "new_vulnerabilities": new_vulnerabilities,
                "error_message": error_message,
                "scan_duration": scan_duration,
            }).execute()
        except Exception as e:
            logger.warning("scan_log insert failed (%s): %s", oem_name, e)
