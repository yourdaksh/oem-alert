from scrapers.base import RSSScraper
import re

class CitrixScraper(RSSScraper):
    """Scraper for Citrix Security Bulletins"""
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product from Citrix bulletin"""
        # Titles: "Citrix ADC and Citrix Gateway Security Bulletin..."
        
        if "Citrix ADC" in title:
            return "Citrix ADC"
        if "Citrix Gateway" in title:
            return "Citrix Gateway"
        if "XenServer" in title:
            return "Citrix Hypervisor (XenServer)"
            
        return super().extract_product_name(title, description)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
