"""IBM scraper — KEV-backed (ibm.com support URLs 404 frequently)."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for

class IBMScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["IBM"], oem_label="IBM")
