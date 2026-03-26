from scrapers.base import RSSScraper
import re

class FortinetScraper(RSSScraper):
    """Scraper for FortiGuard Labs PSIRT (Fortinet)"""
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product from Fortinet advisory"""
        # Titles: "FortiClientMac - Arbitrary file deletion"
        # "FortiOS - Out-of-bounds Write in HTTP daemon"
        
        parts = title.split(' - ')
        if len(parts) > 1:
            return parts[0].strip()
            
        return super().extract_product_name(title, description)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
