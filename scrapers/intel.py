"""
Intel Security Center scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class IntelScraper(RSSScraper):
    """Scraper for Intel Security Center"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Intel vulnerabilities"""
        vulnerabilities = []
        
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_rss_feed(rss_url))
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_intel_page(soup))
        
        return vulnerabilities
    
    def parse_intel_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Intel security page"""
        vulnerabilities = []
        
        try:
            cve_text_elements = soup.find_all(string=lambda x: x and 'CVE-' in x)
            
            for cve_text in cve_text_elements:
                try:
                    cve_match = re.search(r'CVE-\d{4}-\d{4,7}', cve_text)
                    if not cve_match:
                        continue
                    
                    cve_id = cve_match.group(0)
                    
                    parent = cve_text.parent
                    if not parent:
                        continue
                    
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or parent
                    title = title_elem.get_text().strip() if title_elem else cve_id
                    
                    desc_elem = parent.find(['p', 'div', 'span'], class_=re.compile(r'description|summary|content', re.I))
                    if not desc_elem:
                        desc_text = parent.get_text()
                        description = desc_text.replace(title, '').strip()
                    else:
                        description = desc_elem.get_text().strip()
                    
                    severity = self.extract_intel_severity(parent)
                    
                    product_name = self.extract_intel_product(title, description)
                    
                    date_elem = parent.find(['time', 'span', 'div'], class_=re.compile(r'date|published|updated', re.I))
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    cvss_score = self.extract_cvss_score(parent.get_text())
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id,
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=self.oem_config.get('vulnerability_url'),
                        cvss_score=cvss_score
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Intel CVE text: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Intel page: {e}")
        
        return vulnerabilities
    
    def extract_intel_severity(self, element) -> str:
        """Extract severity from Intel vulnerability element"""
        text = element.get_text().lower()
        
        if 'critical' in text:
            return 'Critical'
        elif 'high' in text:
            return 'High'
        elif 'medium' in text:
            return 'Medium'
        elif 'low' in text:
            return 'Low'
        else:
            return 'Unknown'
    
    def extract_intel_product(self, title: str, description: str) -> str:
        """Extract product name from Intel vulnerability"""
        text = (title + " " + description).lower()
        
        products = [
            'cpu', 'processor', 'xeon', 'core', 'pentium', 'celeron', 'atom',
            'graphics', 'gpu', 'integrated graphics', 'wifi', 'bluetooth',
            'ethernet', 'chipset', 'bios', 'uefi', 'sgx', 'txe', 'amt',
            'management engine', 'converged security', 'trusted execution'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Intel Product"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from Intel text"""
        return self.extract_intel_severity(type('obj', (object,), {'get_text': lambda self: text})())
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from Intel RSS item"""
        return self.extract_intel_product(title, description)
