"""
Palo Alto Networks Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class PaloAltoScraper(RSSScraper):
    """Scraper for Palo Alto Networks Security Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Palo Alto vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_paloalto_page(soup))
        
        return vulnerabilities
    
    def parse_paloalto_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Palo Alto security page"""
        vulnerabilities = []
        
        try:
            # Look for CVE entries or advisory links
            cve_links = soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}', re.I))
            
            for cve_link in cve_links[:50]:
                try:
                    cve_text = cve_link.text.strip()
                    href = cve_link.get('href', '')
                    
                    # Extract CVE ID - ensure it's just the CVE number
                    cve_match = re.search(r'CVE-\d{4}-\d{4,7}', cve_text + " " + href, re.I)
                    if cve_match:
                        cve_id = cve_match.group(0)
                    else:
                        # Try to extract from href
                        cve_id = href.split('/')[-1] if '/' in href else cve_text
                        if not cve_id.startswith('CVE-'):
                            continue
                    
                    # Ensure unique_id is max 50 characters (database constraint)
                    cve_id = cve_id[:50]
                    
                    parent = cve_link.find_parent(['div', 'section', 'article', 'tr', 'td'])
                    if not parent:
                        continue
                    
                    title = parent.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    title = title.text.strip() if title else cve_id
                    
                    desc = parent.find('p') or parent.find('div', class_=re.compile(r'description', re.I))
                    description = desc.text.strip() if desc else title
                    
                    severity = self.extract_severity_from_text(title + " " + description)
                    product_name = self.extract_product_name(title, description)
                    
                    published_date = datetime.now()
                    date_elem = parent.find('time') or parent.find('span', class_=re.compile(r'date', re.I))
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id,
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=cve_link.get('href')
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Palo Alto CVE: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Palo Alto page: {e}")
        
        return vulnerabilities
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract Palo Alto product name"""
        text = (title + " " + description).lower()
        
        products = [
            'palo alto', 'pan-os', 'panos', 'prisma', 'cortex',
            'wildfire', 'traps', 'globalprotect', 'panorama',
            'vm-series', 'pa-series', 'cloud-delivered security'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        return "Palo Alto Networks Product"
