"""
Cisco Security Advisories scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import WebScraper
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class CiscoScraper(WebScraper):
    """Scraper for Cisco Security Advisories"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Cisco vulnerabilities"""
        vulnerabilities = []
        
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url, use_selenium=True)
            if soup:
                vulnerabilities.extend(self.parse_cisco_page(soup))
        
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_cisco_rss(rss_url))
        
        return vulnerabilities
    
    def parse_cisco_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Cisco security page"""
        vulnerabilities = []
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:]:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 3:
                            continue
                        
                        advisory_text = cells[0].get_text().strip()
                        cve_id = self.extract_cve_id(advisory_text)
                        
                        if not cve_id:
                            cve_id = f"cisco-{hash(advisory_text) % 100000}"
                        
                        severity = self.extract_cisco_severity(row)
                        
                        product_info = cells[1].get_text().strip() if len(cells) > 1 else "Cisco Product"
                        
                        date_text = cells[2].get_text().strip() if len(cells) > 2 else ""
                        published_date = self.parse_date(date_text) or datetime.now()
                        
                        cvss_score = self.extract_cvss_score(row.get_text())
                        
                        link_elem = row.find('a', href=True)
                        source_url = link_elem['href'] if link_elem else None
                        if source_url and not source_url.startswith('http'):
                            source_url = self.base_url + source_url
                        
                        vuln_record = self.create_vulnerability_record(
                            unique_id=cve_id,
                            product_name=product_info,
                            product_version=None,
                            severity_level=severity,
                            vulnerability_description=advisory_text,
                            mitigation_strategy=None,
                            published_date=published_date,
                            source_url=source_url,
                            cvss_score=cvss_score
                        )
                        
                        vulnerabilities.append(vuln_record)
                        
                    except Exception as e:
                        logger.error(f"Error parsing Cisco table row: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error parsing Cisco page: {e}")
        
        return vulnerabilities
    
    def parse_cisco_rss(self, rss_url: str) -> List[Dict[str, Any]]:
        """Parse Cisco RSS feed"""
        vulnerabilities = []
        
        try:
            response = self.session.get(rss_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            for item in items:
                try:
                    title = item.find('title').text if item.find('title') else ""
                    description = item.find('description').text if item.find('description') else ""
                    link = item.find('link').text if item.find('link') else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') else ""
                    
                    cve_id = self.extract_cve_id(title + " " + description)
                    if not cve_id:
                        cve_id = f"cisco-{hash(title) % 100000}"
                    
                    published_date = self.parse_date(pub_date)
                    if not published_date:
                        published_date = datetime.now()
                    
                    severity = self.extract_cisco_severity_from_text(title + " " + description)
                    
                    product_name = self.extract_cisco_product(title, description)
                    
                    vuln_record = self.create_vulnerability_record(
                        unique_id=cve_id,
                        product_name=product_name,
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=description,
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=link
                    )
                    
                    vulnerabilities.append(vuln_record)
                    
                except Exception as e:
                    logger.error(f"Error parsing Cisco RSS item: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Cisco RSS feed: {e}")
        
        return vulnerabilities
    
    def extract_cisco_severity(self, element) -> str:
        """Extract severity from Cisco vulnerability element"""
        text = element.get_text().lower()
        
        if any(word in text for word in ['critical', 'high severity']):
            return 'Critical'
        elif any(word in text for word in ['high', 'medium-high']):
            return 'High'
        elif any(word in text for word in ['medium', 'medium severity']):
            return 'Medium'
        elif any(word in text for word in ['low', 'low severity', 'informational']):
            return 'Low'
        else:
            return 'Unknown'
    
    def extract_cisco_severity_from_text(self, text: str) -> str:
        """Extract severity from Cisco text"""
        return self.extract_cisco_severity(type('obj', (object,), {'get_text': lambda self: text})())
    
    def extract_cisco_product(self, title: str, description: str) -> str:
        """Extract product name from Cisco vulnerability"""
        text = (title + " " + description).lower()
        
        products = [
            'ios', 'ios xe', 'ios xr', 'nx-os', 'asa', 'firepower',
            'catalyst', 'nexus', 'meraki', 'umbrella', 'duo',
            'webex', 'collaboration', 'routers', 'switches',
            'wireless', 'access points', 'security', 'firewall',
            'vpn', 'identity services', 'prime', 'dna center'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Cisco Product"
