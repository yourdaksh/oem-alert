"""SAP scraper — KEV-backed (support.sap.com requires login)."""
from typing import Any, Dict, List
from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for

class SAPScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["SAP"], oem_label="SAP")
