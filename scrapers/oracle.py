"""
Oracle Security Alerts scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class OracleScraper(RSSScraper):
    """Scraper for Oracle Security Alerts"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Oracle vulnerabilities"""
        vulnerabilities = []
        
        # Try RSS feed first
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_rss_feed(rss_url))
        
        # Also scrape the main security alerts page
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_oracle_page(soup))
        
        return vulnerabilities
    
    def parse_oracle_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Oracle security alerts page"""
        vulnerabilities = []
        
        try:
            # Look for CVE text directly since we found CVE content
            cve_text_elements = soup.find_all(string=lambda x: x and 'CVE-' in x)
            
            for cve_text in cve_text_elements:
                try:
                    # Extract CVE ID from text
                    cve_match = re.search(r'CVE-\d{4}-\d{4,7}', cve_text)
                    if not cve_match:
                        continue
                    
                    cve_id = cve_match.group(0)
                    
                    # Get the parent element for context
                    parent = cve_text.parent
                    if not parent:
                        continue
                    
                    # Extract title/description
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or parent
                    title = title_elem.get_text().strip() if title_elem else cve_id
                    
                    # Extract description from surrounding text
                    desc_elem = parent.find(['p', 'div', 'span'], class_=re.compile(r'description|summary|content', re.I))
                    if not desc_elem:
                        desc_text = parent.get_text()
                        description = desc_text.replace(title, '').strip()
                    else:
                        description = desc_elem.get_text().strip()
                    
                    # Extract severity
                    severity = self.extract_oracle_severity(parent)
                    
                    # Extract product information
                    product_name = self.extract_oracle_product(title, description)
                    
                    # Extract published date
                    date_elem = parent.find(['time', 'span', 'div'], class_=re.compile(r'date|published|updated', re.I))
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    # Extract CVSS score
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
                    logger.error(f"Error parsing Oracle CVE text: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Oracle page: {e}")
        
        return vulnerabilities
    
    def extract_oracle_severity(self, element) -> str:
        """Extract severity from Oracle vulnerability element"""
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
    
    def extract_oracle_product(self, title: str, description: str) -> str:
        """Extract product name from Oracle vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Oracle products
        products = [
            'database', 'oracle db', 'mysql', 'java', 'jdk', 'jre', 'weblogic',
            'fusion middleware', 'apex', 'forms', 'reports', 'goldengate',
            'data integrator', 'business intelligence', 'hyperion', 'peoplesoft',
            'siebel', 'jde', 'retail', 'communications', 'financial services',
            'health sciences', 'utilities', 'construction', 'engineering',
            'hospitality', 'media', 'public sector', 'transportation'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Oracle Product"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from Oracle text"""
        return self.extract_oracle_severity(type('obj', (object,), {'get_text': lambda self: text})())
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from Oracle RSS item"""
        return self.extract_oracle_product(title, description)
