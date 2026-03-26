from scrapers.base import RSSScraper
import re

class VMwareScraper(RSSScraper):
    """Scraper for VMware Security Advisories"""
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product from VMware advisory"""
        # Titles: "VMSA-2024-0001: VMware vCenter Server updates address..."
        
        match = re.search(r'VMware\s+([a-zA-Z0-9\s]+?)(?:updates|addresses|vulnerability)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        return super().extract_product_name(title, description)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
