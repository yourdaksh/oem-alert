"""
Microsoft Security Response Center scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class MicrosoftScraper(RSSScraper):
    """Scraper for Microsoft Security Response Center"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Microsoft vulnerabilities"""
        vulnerabilities = []
        
        # Scrape the MSRC update guide page
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_microsoft_page(soup))
        
        return vulnerabilities
    
    def parse_microsoft_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Microsoft security update page"""
        vulnerabilities = []
        
        try:
            # Look for CVE entries in links
            cve_links = soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}', re.I))
            
            # Also look for CVE text in page content
            cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}')
            cve_texts = soup.find_all(string=cve_pattern)
            
            processed_cves = set()
            
            # Process links first
            for cve_link in cve_links[:50]:
                try:
                    cve_id = cve_link.text.strip() or cve_link.get('href', '').split('/')[-1]
                    cve_match = cve_pattern.search(cve_id)
                    if cve_match:
                        cve_id = cve_match.group(0)
                    else:
                        continue
                    
                    if cve_id in processed_cves:
                        continue
                    processed_cves.add(cve_id)
                    
                    # Find parent container
                    parent = cve_link.find_parent(['div', 'section', 'article', 'tr', 'td'])
                    if not parent:
                        continue
                    
                    # Extract title/description
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    title = title_elem.text.strip() if title_elem else cve_id
                    
                    desc_elem = parent.find('p') or parent.find('div', class_=re.compile(r'description|summary', re.I))
                    description = desc_elem.text.strip() if desc_elem else title
                    
                    # Extract severity
                    severity = self.extract_severity_from_text(title + " " + description)
                    
                    # Extract product
                    product_name = self.extract_product_name(title, description)
                    
                    # Extract date
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
                    logger.error(f"Error parsing Microsoft CVE: {e}")
                    continue
            
            # Process text content for CVEs
            for cve_text in cve_texts[:50]:
                try:
                    cve_match = cve_pattern.search(cve_text)
                    if not cve_match:
                        continue
                    
                    cve_id = cve_match.group(0)
                    if cve_id in processed_cves:
                        continue
                    processed_cves.add(cve_id)
                    
                    parent = cve_text.parent
                    while parent and parent.name not in ['div', 'section', 'article', 'tr', 'td', 'li', 'p']:
                        parent = parent.parent
                    
                    if not parent:
                        continue
                    
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'strong', 'a'])
                    title = title_elem.text.strip() if title_elem else cve_id
                    
                    desc_elem = parent.find('p') or parent.find('div', class_=re.compile(r'description|summary', re.I))
                    description = desc_elem.text.strip() if desc_elem else parent.get_text()[:500]
                    
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
                        unique_id=cve_id[:50],
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=self.oem_config.get('vulnerability_url')
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Microsoft CVE text: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Microsoft page: {e}")
        
        return vulnerabilities
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract Microsoft product name"""
        text = (title + " " + description).lower()
        
        products = [
            'windows', 'office', 'azure', 'exchange', 'sharepoint',
            'sql server', 'visual studio', 'edge', 'internet explorer',
            'outlook', 'word', 'excel', 'powerpoint', 'teams',
            'onedrive', 'dynamics', 'power bi', 'active directory'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        return "Microsoft Product"
