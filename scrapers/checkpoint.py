"""
Check Point Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class CheckPointScraper(RSSScraper):
    """Scraper for Check Point Security Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Check Point vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_checkpoint_page(soup))
        
        return vulnerabilities
    
    def parse_checkpoint_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Check Point security advisories page"""
        vulnerabilities = []
        
        try:
            cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}')
            processed_cves = set()
            
            # Look for CVE in links first
            cve_links = soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}', re.I))
            for cve_link in cve_links[:100]:
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
                    
                    parent = cve_link.find_parent(['div', 'section', 'article', 'tr', 'td', 'li'])
                    if not parent:
                        continue
                    
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    title = title_elem.get_text().strip() if title_elem else cve_id
                    
                    desc_elem = parent.find(['p', 'div'], class_=re.compile(r'description|summary', re.I))
                    description = desc_elem.get_text().strip() if desc_elem else parent.get_text()[:500]
                    
                    severity = self.extract_severity_from_text(title + " " + description)
                    product_name = self.extract_product_name(title, description)
                    
                    date_elem = parent.find(['time', 'span'], class_=re.compile(r'date', re.I))
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    cvss_score = self.extract_cvss_score(parent.get_text())
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id[:50],
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=f"{title}\n\n{description}",
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=cve_link.get('href') or self.oem_config.get('vulnerability_url'),
                        cvss_score=cvss_score
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Check Point CVE link: {e}")
                    continue
            
            # Also look for CVE text in page content
            cve_texts = soup.find_all(string=cve_pattern)
            
            for cve_text in cve_texts[:100]:
                try:
                    cve_match = cve_pattern.search(cve_text)
                    if not cve_match:
                        continue
                    
                    cve_id = cve_match.group(0)
                    if cve_id in processed_cves:
                        continue
                    processed_cves.add(cve_id)
                    
                    parent = cve_text.parent
                    while parent and parent.name not in ['div', 'article', 'section', 'tr', 'td', 'li']:
                        parent = parent.parent
                    
                    if not parent:
                        continue
                    
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    title = title_elem.get_text().strip() if title_elem else cve_id
                    
                    desc_elem = parent.find(['p', 'div'], class_=re.compile(r'description|summary', re.I))
                    description = desc_elem.get_text().strip() if desc_elem else parent.get_text()[:500]
                    
                    severity = self.extract_severity_from_text(title + " " + description)
                    product_name = self.extract_product_name(title, description)
                    
                    date_elem = parent.find(['time', 'span'], class_=re.compile(r'date', re.I))
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    cvss_score = self.extract_cvss_score(parent.get_text())
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id[:50],
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
                    logger.error(f"Error parsing Check Point CVE: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Check Point page: {e}")
        
        return vulnerabilities
