"""
Cisco Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import WebScraper
import logging

logger = logging.getLogger(__name__)

class CiscoScraper(WebScraper):
    """Scraper for Cisco Security Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Cisco vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_cisco_page(soup))
        
        return vulnerabilities
    
    def parse_cisco_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Cisco security advisories page"""
        vulnerabilities = []
        
        try:
            # Look for advisory entries
            advisory_rows = soup.find_all('tr', class_=re.compile(r'advisory|security', re.I))
            
            for row in advisory_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                    
                    # Extract advisory ID
                    advisory_link = cells[0].find('a')
                    if not advisory_link:
                        continue
                    
                    advisory_id = advisory_link.text.strip()
                    
                    # Extract title/description
                    title = cells[1].text.strip() if len(cells) > 1 else ""
                    
                    # Extract severity
                    severity_text = cells[2].text.strip() if len(cells) > 2 else ""
                    severity = self.normalize_severity(severity_text)
                    
                    # Extract published date
                    published_date = datetime.now()
                    if len(cells) > 3:
                        date_text = cells[3].text.strip()
                        parsed_date = self.parse_date(date_text)
                        if parsed_date:
                            published_date = parsed_date
                    
                    # Extract CVE IDs from the advisory
                    cve_ids = self.extract_cve_ids_from_text(title + " " + advisory_id)
                    
                    # Extract product information
                    product_name = self.extract_cisco_product(title)
                    
                    # Create vulnerability record for each CVE
                    for cve_id in cve_ids:
                        vuln_record = self.create_vulnerability_record(
                            unique_id=cve_id,
                            product_name=product_name,
                            product_version=None,
                            severity_level=severity,
                            vulnerability_description=title,
                            mitigation_strategy=None,
                            published_date=published_date,
                            source_url=advisory_link.get('href')
                        )
                        
                        vulnerabilities.append(vuln_record)
                    
                    # If no CVE found, create one with advisory ID
                    if not cve_ids:
                        vuln_record = self.create_vulnerability_record(
                            unique_id=advisory_id,
                            product_name=product_name,
                            product_version=None,
                            severity_level=severity,
                            vulnerability_description=title,
                            mitigation_strategy=None,
                            published_date=published_date,
                            source_url=advisory_link.get('href')
                        )
                        
                        vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Cisco advisory row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Cisco page: {e}")
        
        return vulnerabilities
    
    def extract_cve_ids_from_text(self, text: str) -> List[str]:
        """Extract all CVE IDs from text"""
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        return re.findall(cve_pattern, text, re.IGNORECASE)
    
    def extract_cisco_product(self, title: str) -> str:
        """Extract product name from Cisco advisory title"""
        text = title.lower()
        
        # Common Cisco products
        products = [
            'ios', 'ios xe', 'ios xr', 'nx-os', 'asa', 'firepower', 'catalyst',
            'meraki', 'webex', 'ucs', 'apic', 'aci', 'ise', 'wlc', 'prime',
            'dna center', 'sd-wan', 'umbrella', 'duo', 'talos'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Cisco Product"
    
    def find_vulnerability_elements(self, soup) -> List:
        """Find Cisco vulnerability elements"""
        # Look for advisory tables
        tables = soup.find_all('table')
        elements = []
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Has enough columns for advisory data
                    elements.append(row)
        
        return elements
    
    def parse_vulnerability_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse Cisco vulnerability element"""
        try:
            cells = element.find_all('td')
            if len(cells) < 3:
                return None
            
            # Extract advisory information
            advisory_link = cells[0].find('a')
            if not advisory_link:
                return None
            
            advisory_id = advisory_link.text.strip()
            title = cells[1].text.strip() if len(cells) > 1 else ""
            severity_text = cells[2].text.strip() if len(cells) > 2 else ""
            
            # Extract CVE IDs
            cve_ids = self.extract_cve_ids_from_text(title + " " + advisory_id)
            if not cve_ids:
                return None
            
            # Use first CVE ID
            cve_id = cve_ids[0]
            
            # Extract published date
            published_date = datetime.now()
            if len(cells) > 3:
                date_text = cells[3].text.strip()
                parsed_date = self.parse_date(date_text)
                if parsed_date:
                    published_date = parsed_date
            
            vuln_record = self.create_vulnerability_record(
                unique_id=cve_id,
                product_name=self.extract_cisco_product(title),
                product_version=None,
                severity_level=self.normalize_severity(severity_text),
                vulnerability_description=title,
                mitigation_strategy=None,
                published_date=published_date,
                source_url=advisory_link.get('href')
            )
            
            return vuln_record
            
        except Exception as e:
            logger.error(f"Error parsing Cisco vulnerability element: {e}")
            return None
