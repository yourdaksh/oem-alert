from scrapers.base import RSSScraper
import re
from datetime import datetime

class RedHatScraper(RSSScraper):
    """Scraper for Red Hat Security Advisories"""
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from RHSA title"""
        # Format often: "Important: chromium-browser security update" or "Moderate: kernel security update"
        # We want to extract "chromium-browser" or "kernel"
        
        # Remove severity prefix if present (e.g., "Important: ")
        clean_title = re.sub(r'^(Important|Moderate|Low|Critical):\s+', '', title, flags=re.IGNORECASE)
        
        # Extract product name (usually before "security update" or "update")
        match = re.search(r'(.+?)\s+(?:security\s+)?update', clean_title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        return super().extract_product_name(title, description)

    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from RHSA title"""
        # RHSA titles usually start with severity: "Important: ..."
        match = re.search(r'^(Important|Moderate|Low|Critical)', text, re.IGNORECASE)
        if match:
            return self.normalize_severity(match.group(1))
        return super().extract_severity_from_text(text)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
