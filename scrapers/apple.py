"""
Apple Security Updates scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import WebScraper
import logging

logger = logging.getLogger(__name__)

class AppleScraper(WebScraper):
    """Scraper for Apple Security Updates"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Apple vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_apple_page(soup))
        
        return vulnerabilities
    
    def parse_apple_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Apple security page"""
        vulnerabilities = []
        
        try:
            # Look for security update entries
            update_sections = soup.find_all('div', class_=re.compile(r'update|security|advisory', re.I))
            
            for section in update_sections:
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
                        severity = self.extract_apple_severity(parent)
                        
                        # Extract product information
                        product_name = self.extract_apple_product(title, description)
                        
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
                    logger.error(f"Error parsing Apple update section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Apple page: {e}")
        
        return vulnerabilities
    
    def extract_apple_severity(self, element) -> str:
        """Extract severity from Apple vulnerability element"""
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
    
    def extract_apple_product(self, title: str, description: str) -> str:
        """Extract product name from Apple vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Apple products
        products = [
            'ios', 'iphone os', 'macos', 'mac os x', 'mac os',
            'watchos', 'watch os', 'tvos', 'tv os',
            'safari', 'webkit', 'xcode', 'itunes',
            'icloud', 'app store', 'mac app store',
            'airpods', 'airtag', 'homepod',
            'iphone', 'ipad', 'macbook', 'imac', 'mac pro',
            'mac mini', 'apple tv', 'apple watch',
            'core foundation', 'core graphics', 'core text',
            'foundation', 'uikit', 'appkit', 'swift',
            'objective-c', 'metal', 'opengl', 'opencv'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Apple Product"
    
    def find_vulnerability_elements(self, soup) -> List:
        """Find Apple vulnerability elements"""
        # Look for update sections
        update_sections = soup.find_all('div', class_=re.compile(r'update|security', re.I))
        return update_sections
    
    def parse_vulnerability_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse Apple vulnerability element"""
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
                product_name=self.extract_apple_product(title, description),
                product_version=None,
                severity_level=self.extract_apple_severity(element),
                vulnerability_description=f"{title}\n\n{description}",
                mitigation_strategy=None,
                published_date=datetime.now(),
                source_url=cve_link.get('href')
            )
            
            return vuln_record
            
        except Exception as e:
            logger.error(f"Error parsing Apple vulnerability element: {e}")
            return None
