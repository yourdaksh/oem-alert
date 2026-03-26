<<<<<<< HEAD
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
=======
"""
Fortinet PSIRT Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class FortinetScraper(RSSScraper):
    """Scraper for Fortinet PSIRT Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Fortinet vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_fortinet_page(soup))
        
        return vulnerabilities
    
    def parse_fortinet_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Fortinet PSIRT page"""
        vulnerabilities = []
        
        try:
            cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}')
            processed_cves = set()
            
            # Look for CVE entries or advisory links
            cve_links = soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}', re.I))
            
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
                    logger.error(f"Error parsing Fortinet CVE: {e}")
                    continue
            
            # Also look for CVE text in page content
            cve_texts = soup.find_all(string=cve_pattern)
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
                    while parent and parent.name not in ['div', 'section', 'article', 'tr', 'td']:
                        parent = parent.parent
                    
                    if not parent:
                        continue
                    
                    title = parent.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    title = title.text.strip() if title else cve_id
                    
                    desc = parent.find('p') or parent.find('div', class_=re.compile(r'description', re.I))
                    description = desc.text.strip() if desc else parent.get_text()[:500]
                    
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
                    logger.error(f"Error parsing Fortinet CVE text: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Fortinet page: {e}")
        
        return vulnerabilities
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract Fortinet product name"""
        text = (title + " " + description).lower()
        
        products = [
            'fortigate', 'fortinet', 'fortios', 'fortisandbox',
            'fortimanager', 'fortianalyzer', 'forticlient', 'fortiap',
            'fortiedr', 'fortinac', 'fortivoice', 'fortimail'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        return "Fortinet Product"
>>>>>>> origin/main
