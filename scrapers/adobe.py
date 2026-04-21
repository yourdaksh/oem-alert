"""Adobe scraper — KEV-backed (helpx.adobe.com times out and advisory pages need JS)."""
from typing import Any, Dict, List

from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for


class AdobeScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Adobe"], oem_label="Adobe")
