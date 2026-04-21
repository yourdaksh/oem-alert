"""
Microsoft scraper — backed by the CISA Known Exploited Vulnerabilities catalog.

MSRC's public pages require auth or render only with JS, so this scraper falls
through to the KEV feed which reliably covers Microsoft products (368 entries
at last count).
"""
from typing import Any, Dict, List

from scrapers.base import RSSScraper
from scrapers._cisa_kev import kev_records_for


class MicrosoftScraper(RSSScraper):
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        return kev_records_for(["Microsoft"], oem_label="Microsoft")
