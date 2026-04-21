"""Dell scraper — KEV-backed."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for

class DellScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Dell"], oem_label="Dell")
