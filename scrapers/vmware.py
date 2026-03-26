<<<<<<< HEAD
from scrapers.base import RSSScraper
import re
=======
"""
VMware Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)
>>>>>>> origin/main

class VMwareScraper(RSSScraper):
    """Scraper for VMware Security Advisories"""
    
<<<<<<< HEAD
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product from VMware advisory"""
        # Titles: "VMSA-2024-0001: VMware vCenter Server updates address..."
        
        match = re.search(r'VMware\s+([a-zA-Z0-9\s]+?)(?:updates|addresses|vulnerability)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        return super().extract_product_name(title, description)

    def scrape_vulnerabilities(self):
        """Scrape vulnerabilities from RSS feed"""
        rss_url = self.oem_config.get('rss_url')
        if not rss_url:
            return []
        
        return self.parse_rss_feed(rss_url)
=======
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape VMware vulnerabilities"""
        vulnerabilities = []
        
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
            cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}')
            vmsa_pattern = re.compile(r'VMSA-\d{4}-\d{4,7}')
            processed_ids = set()
            
            # Look for CVE entries or advisory links
            cve_links = soup.find_all('a', href=re.compile(r'(CVE-\d{4}-\d{4,7}|VMSA-\d{4}-\d{4,7})', re.I))
            
            for link in cve_links[:50]:
                try:
                    link_text = link.text.strip()
                    href = link.get('href', '')
                    
                    # Extract CVE or VMSA ID
                    cve_match = cve_pattern.search(link_text + " " + href)
                    vmsa_match = vmsa_pattern.search(link_text + " " + href)
                    
                    unique_id = cve_match.group(0) if cve_match else (vmsa_match.group(0) if vmsa_match else None)
                    if not unique_id:
                        continue
                    
                    if unique_id in processed_ids:
                        continue
                    processed_ids.add(unique_id)
                    
                    parent = link.find_parent(['div', 'section', 'article', 'tr', 'td', 'li'])
                    if not parent:
                        continue
                    
                    title = parent.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    title = title.text.strip() if title else link_text
                    
                    desc = parent.find('p') or parent.find('div', class_=re.compile(r'description|summary', re.I))
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
                        unique_id=unique_id,
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=href if href.startswith('http') else None
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing VMware advisory: {e}")
                    continue
            
            # Also look for CVE text in page content
            cve_texts = soup.find_all(string=cve_pattern)
            for cve_text in cve_texts[:50]:
                try:
                    cve_match = cve_pattern.search(cve_text)
                    if not cve_match:
                        continue
                    
                    cve_id = cve_match.group(0)
                    if cve_id in processed_ids:
                        continue
                    processed_ids.add(cve_id)
                    
                    parent = cve_text.parent
                    while parent and parent.name not in ['div', 'section', 'article', 'tr', 'td', 'li']:
                        parent = parent.parent
                    
                    if not parent:
                        continue
                    
                    title = parent.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    title = title.text.strip() if title else cve_id
                    
                    desc = parent.find('p') or parent.find('div', class_=re.compile(r'description|summary', re.I))
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
                    logger.error(f"Error parsing VMware CVE text: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing VMware page: {e}")
        
        return vulnerabilities
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract VMware product name"""
        text = (title + " " + description).lower()
        
        products = [
            'vsphere', 'esxi', 'vcenter', 'vcenter server', 'nsx',
            'vrealize', 'horizon', 'workspace one', 'carbon black',
            'tanzu', 'cloud foundation', 'vcloud', 'airwatch'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        return "VMware Product"
>>>>>>> origin/main
