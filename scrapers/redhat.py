"""
Red Hat Security Advisories scraper — hits the official Red Hat security-data JSON API.

The previous HTML-parsing implementation returned zero rows because access.redhat.com
moved its security pages to a SPA that only renders with JavaScript. Using the Hydra
JSON feed is faster, paginated, and doesn't need a browser.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from scrapers.base import RSSScraper


logger = logging.getLogger(__name__)

CVE_API = "https://access.redhat.com/hydra/rest/securitydata/cve.json"
PER_PAGE = 50


class RedHatScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        try:
            res = self.session.get(CVE_API, params={"per_page": PER_PAGE}, timeout=30)
            res.raise_for_status()
            items = res.json()
        except Exception as e:
            logger.error("Red Hat CVE feed fetch failed: %s", e)
            return []

        vulnerabilities: List[Dict[str, Any]] = []
        for item in items:
            cve_id = item.get("CVE")
            if not cve_id:
                continue

            severity = (item.get("severity") or "Unknown").capitalize()
            cvss = item.get("cvss3_score") or item.get("cvss_score")
            published = item.get("public_date") or datetime.utcnow().isoformat()
            try:
                published_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except Exception:
                published_date = datetime.utcnow()

            description = item.get("bugzilla_description") or item.get("advisories") or cve_id
            if isinstance(description, list):
                description = "; ".join(str(x) for x in description)

            package = item.get("affected_packages") or []
            product_name = package[0] if package else "Red Hat"

            vulnerabilities.append(self.create_vulnerability_record(
                unique_id=cve_id,
                product_name=product_name,
                product_version=None,
                severity_level=severity,
                vulnerability_description=str(description)[:2000],
                mitigation_strategy=None,
                published_date=published_date,
                source_url=item.get("resource_url") or f"https://access.redhat.com/security/cve/{cve_id}",
                cvss_score=str(cvss) if cvss else None,
                affected_versions=", ".join(package) if package else None,
            ))

        logger.info("Red Hat: scraped %d CVEs from JSON feed", len(vulnerabilities))
        return vulnerabilities
