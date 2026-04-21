"""Apple scraper — KEV-backed.

The previous implementation scraped developer.apple.com news articles (policy
updates, app review announcements) which aren't vulnerabilities. KEV filtered
by vendor Apple gives us the actual exploited CVEs affecting Apple products.
"""
from typing import Any, Dict, List

from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for


class AppleScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Apple"], oem_label="Apple")
