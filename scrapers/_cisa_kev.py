"""
Shared helper that serves the CISA Known Exploited Vulnerabilities catalog.

Many vendor sites (Microsoft's MSRC, Apache, VMware, Dell, Citrix, SAP...) either
render only with JavaScript or return 404 for the scraper URLs we were using.
CISA's KEV catalog covers the overlap — a single ~200KB JSON file lists every
vulnerability known to be exploited in the wild, tagged by vendor — and it's
arguably more actionable than a full CVE dump.
"""
import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

import requests


logger = logging.getLogger(__name__)

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


@lru_cache(maxsize=1)
def _fetch_kev() -> List[Dict[str, Any]]:
    """Cache the catalog in-process; a single run typically calls it per-vendor."""
    try:
        r = requests.get(KEV_URL, timeout=30)
        r.raise_for_status()
        return r.json().get("vulnerabilities", [])
    except Exception as e:
        logger.error("CISA KEV fetch failed: %s", e)
        return []


def kev_records_for(vendor_keys: List[str], oem_label: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Return vulnerability dicts for any KEV entry whose vendorProject matches.

    `vendor_keys` is a case-insensitive list of vendor names to match. `oem_label`
    is what we stamp on the output (so the API can filter by the org's OEM list).
    """
    keys = {k.lower() for k in vendor_keys}
    out: List[Dict[str, Any]] = []
    for v in _fetch_kev():
        if (v.get("vendorProject") or "").lower() not in keys:
            continue
        try:
            pub = datetime.fromisoformat(v.get("dateAdded"))
        except Exception:
            pub = datetime.utcnow()
        out.append({
            "unique_id": v.get("cveID"),
            "product_name": v.get("product") or oem_label,
            "product_version": None,
            "oem_name": oem_label,
            "severity_level": "Critical",
            "vulnerability_description": v.get("shortDescription") or v.get("vulnerabilityName") or v.get("cveID"),
            "mitigation_strategy": v.get("requiredAction"),
            "published_date": pub,
            "source_url": f"https://nvd.nist.gov/vuln/detail/{v.get('cveID')}",
            "cvss_score": None,
            "affected_versions": v.get("product"),
        })
        if len(out) >= limit:
            break
    return out
