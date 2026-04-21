"""HP/HPE scraper — KEV-backed (covers both HP and HPE)."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for

class HPEScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Hewlett Packard (HP)", "Hewlett Packard Enterprise (HPE)"], oem_label="HP/HPE")
