"""
Microsoft Security Response Center scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class MicrosoftScraper(RSSScraper):
    """Scraper for Microsoft Security Response Center"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Microsoft vulnerabilities"""
        vulnerabilities = []
        
        # Try RSS feed first
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_rss_feed(rss_url))
        
        # Also scrape the main vulnerability page
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_microsoft_page(soup))
        
        return vulnerabilities
    
    def parse_microsoft_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Microsoft vulnerability page"""
        vulnerabilities = []
        
        try:
            # Look for vulnerability entries
            vuln_entries = soup.find_all('div', class_=re.compile(r'vulnerability|security', re.I))
            
            for entry in vuln_entries:
                try:
                    # Extract CVE ID
                    cve_link = entry.find('a', href=re.compile(r'CVE-\d{4}-\d{4,7}'))
                    if not cve_link:
                        continue
                    
                    cve_id = cve_link.text.strip()
                    
                    # Extract title/description
                    title_elem = entry.find('h3') or entry.find('h2') or entry.find('h1')
                    title = title_elem.text.strip() if title_elem else ""
                    
                    # Extract description
                    desc_elem = entry.find('p') or entry.find('div', class_=re.compile(r'description', re.I))
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Extract severity
                    severity = self.extract_microsoft_severity(entry)
                    
                    # Extract product information
                    product_name = self.extract_microsoft_product(title, description)
                    
                    # Extract published date
                    date_elem = entry.find('time') or entry.find('span', class_=re.compile(r'date', re.I))
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    # Extract CVSS score
                    cvss_score = self.extract_cvss_score(entry.get_text())
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id,
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=cve_link.get('href'),
                        cvss_score=cvss_score
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Microsoft vulnerability entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Microsoft page: {e}")
        
        return vulnerabilities
    
    def extract_microsoft_severity(self, element) -> str:
        """Extract severity from Microsoft vulnerability element"""
        text = element.get_text().lower()
        
        if 'critical' in text:
            return 'Critical'
        elif 'important' in text:
            return 'High'
        elif 'moderate' in text:
            return 'Medium'
        elif 'low' in text:
            return 'Low'
        else:
            return 'Unknown'
    
    def extract_microsoft_product(self, title: str, description: str) -> str:
        """Extract product name from Microsoft vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Microsoft products
        products = [
            'windows', 'office', 'azure', 'exchange', 'sharepoint', 'sql server',
            'visual studio', 'internet explorer', 'edge', 'outlook', 'word',
            'excel', 'powerpoint', 'teams', 'onedrive', 'dynamics', 'power bi'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Microsoft Product"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from Microsoft text"""
        return self.extract_microsoft_severity(type('obj', (object,), {'get_text': lambda self: text})())
