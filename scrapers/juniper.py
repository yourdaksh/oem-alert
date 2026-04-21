"""Juniper scraper — KEV-backed (support portal requires JS)."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for

class JuniperScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Juniper"], oem_label="Juniper Networks")
