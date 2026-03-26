from scrapers.base import RSSScraper
import re

class PaloAltoScraper(RSSScraper):
    """Scraper for Palo Alto Networks Security Advisories"""
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product from PAN-OS advisory title"""
        # Titles are often "PAN-SA-2024-0001 PAN-OS: Vulnerability in..."
        # Or "PAN-SA-2024-0002 Cortez XDR: ..."
        
        parts = title.split(':')
        if len(parts) > 1:
            # Check if part before colon contains product info
            potential_product = parts[0].split(' ')[-1] # Grab last word before colon
            if 'PAN-OS' in parts[0]:
                return 'PAN-OS'
            if 'Cortex' in parts[0]:
                return 'Cortex XDR'
                
        # Fallback to checking description or title for keywords
        if 'PAN-OS' in title or 'PAN-OS' in description:
            return 'PAN-OS'
        if 'GlobalProtect' in title or 'GlobalProtect' in description:
            return 'GlobalProtect'
            
        return super().extract_product_name(title, description)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
