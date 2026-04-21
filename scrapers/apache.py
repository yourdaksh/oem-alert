"""Apache scraper — KEV-backed (HTTP advisory pages don't list machine-readable CVEs)."""
from typing import Any, Dict, List

from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for


class ApacheScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Apache"], oem_label="Apache")
