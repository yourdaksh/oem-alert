"""
Apache HTTP Server Security scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import WebScraper
import logging

logger = logging.getLogger(__name__)

class ApacheScraper(WebScraper):
    """Scraper for Apache HTTP Server Security"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Apache vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_apache_page(soup))
        
        return vulnerabilities
    
    def parse_apache_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Apache security page"""
        vulnerabilities = []
        
        try:
            # Look for security advisory entries
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
                        severity = self.extract_apache_severity(parent)
                        
                        # Extract product information
                        product_name = self.extract_apache_product(title, description)
                        
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
                    logger.error(f"Error parsing Apache advisory section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Apache page: {e}")
        
        return vulnerabilities
    
    def extract_apache_severity(self, element) -> str:
        """Extract severity from Apache vulnerability element"""
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
    
    def extract_apache_product(self, title: str, description: str) -> str:
        """Extract product name from Apache vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Apache products
        products = [
            'httpd', 'http server', 'apache httpd', 'apache http server',
            'tomcat', 'apache tomcat', 'web server',
            'mod_ssl', 'mod_security', 'mod_rewrite',
            'apr', 'apache portable runtime',
            'apr-util', 'apache portable runtime utilities',
            'httpd24', 'httpd22', 'httpd20'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Apache HTTP Server"
    
    def find_vulnerability_elements(self, soup) -> List:
        """Find Apache vulnerability elements"""
        # Look for advisory sections
        advisory_sections = soup.find_all('div', class_=re.compile(r'advisory|security', re.I))
        return advisory_sections
    
    def parse_vulnerability_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse Apache vulnerability element"""
        try:
            # Look for CVE links
            cve_links = element.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}'))
            
            if not cve_links:
                return None
            
            # Use first CVE
            cve_link = cve_links[0]
            cve_id = cve_link.text.strip()
            
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
            title = title_elem.text.strip() if title_elem else ""
            
            # Extract description
            desc_elem = element.find('p') or element.find('div', class_=re.compile(r'description', re.I))
            description = desc_elem.text.strip() if desc_elem else ""
            
            vuln_record = self.create_vulnerability_record(
                unique_id=cve_id,
                product_name=self.extract_apache_product(title, description),
                product_version=None,
                severity_level=self.extract_apache_severity(element),
                vulnerability_description=f"{title}\n\n{description}",
                mitigation_strategy=None,
                published_date=datetime.now(),
                source_url=cve_link.get('href')
            )
            
            return vuln_record
            
        except Exception as e:
            logger.error(f"Error parsing Apache vulnerability element: {e}")
            return None
