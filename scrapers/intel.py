"""Intel scraper — KEV-backed. intel.com blocks bots (403); KEV has Intel entries."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for


class IntelScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Intel"], oem_label="Intel")
