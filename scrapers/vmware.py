"""
VMware Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class VMwareScraper(RSSScraper):
    """Scraper for VMware Security Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape VMware vulnerabilities"""
        vulnerabilities = []
        
        # Try RSS feed first
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_rss_feed(rss_url))
        
        # Also scrape the main security advisories page
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_vmware_page(soup))
        
        return vulnerabilities
    
    def parse_vmware_page(self, soup) -> List[Dict[str, Any]]:
        """Parse VMware security advisories page"""
        vulnerabilities = []
        
        try:
            # Look for advisory entries
            advisory_sections = soup.find_all('div', class_=re.compile(r'advisory|security|vulnerability', re.I))
            
            for section in advisory_sections:
                try:
                    # Look for CVE links
                    cve_links = section.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}'))
                    
                    for cve_link in cve_links:
                        cve_id = cve_link.text.strip()
                        
                        # Find the parent container for this CVE
                        parent = cve_link.find_parent(['div', 'section', 'article'])
                        if not parent:
                            continue
                        
                        # Extract title
                        title_elem = parent.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.text.strip() if title_elem else ""
                        
                        # Extract description
                        desc_elem = parent.find('p') or parent.find('div', class_=re.compile(r'description', re.I))
                        description = desc_elem.text.strip() if desc_elem else ""
                        
                        # Extract severity
                        severity = self.extract_vmware_severity(parent)
                        
                        # Extract product information
                        product_name = self.extract_vmware_product(title, description)
                        
                        # Extract published date
                        published_date = datetime.now()
                        date_elem = parent.find('time') or parent.find('span', class_=re.compile(r'date', re.I))
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
                            source_url=cve_link.get('href'),
                            cvss_score=cvss_score
                        )
                        
                        vulnerabilities.append(vuln_record)
                
                except Exception as e:
                    logger.error(f"Error parsing VMware advisory section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing VMware page: {e}")
        
        return vulnerabilities
    
    def extract_vmware_severity(self, element) -> str:
        """Extract severity from VMware vulnerability element"""
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
    
    def extract_vmware_product(self, title: str, description: str) -> str:
        """Extract product name from VMware vulnerability"""
        text = (title + " " + description).lower()
        
        # Common VMware products
        products = [
            'vsphere', 'esxi', 'vcenter', 'vcenter server', 'vcenter server appliance',
            'vrealize', 'vrealize operations', 'vrealize automation', 'vrealize log insight',
            'horizon', 'horizon view', 'horizon client', 'workspace one',
            'nsx', 'nsx-t', 'nsx data center', 'nsx cloud',
            'tanzu', 'tanzu kubernetes', 'tanzu application service',
            'cloud foundation', 'vcloud', 'vcloud director',
            'fusion', 'workstation', 'player', 'thinapp',
            'carbon black', 'airwatch', 'unified access gateway'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "VMware Product"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from VMware text"""
        return self.extract_vmware_severity(type('obj', (object,), {'get_text': lambda self: text})())
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from VMware RSS item"""
        return self.extract_vmware_product(title, description)
