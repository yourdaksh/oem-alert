"""
Schneider Electric Security Notifications scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class SchneiderScraper(BaseScraper):
    """Scraper for Schneider Electric Security Notifications"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Schneider Electric vulnerabilities"""
        vulnerabilities = []
        
        try:
            soup = self.get_page(self.oem_config.get('vulnerability_url'))
            if not soup:
                return vulnerabilities
            
            # Look for the security notifications table
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 4:
                            continue
                        
                        # Extract data from table cells
                        # Based on search results: Last updated | Title | CVE | Description | Products and Versions affected | PDF | CSAF
                        last_updated = cells[0].get_text().strip()
                        title = cells[1].get_text().strip()
                        cve_cell = cells[2].get_text().strip()
                        description = cells[3].get_text().strip()
                        
                        # Extract CVE IDs from the CVE cell
                        cve_ids = self.extract_cve_ids_from_text(cve_cell)
                        if not cve_ids:
                            continue
                        
                        # Extract severity from title or description
                        severity = self.extract_schneider_severity(title + " " + description)
                        
                        # Extract product information
                        product_name = self.extract_schneider_product(title, description)
                        
                        # Parse published date
                        published_date = datetime.now()
                        parsed_date = self.parse_date(last_updated)
                        if parsed_date:
                            published_date = parsed_date
                        
                        # Extract CVSS score
                        cvss_score = self.extract_cvss_score(description)
                        
                        # Create vulnerability record for each CVE
                        for cve_id in cve_ids:
                            vuln_record = self.create_vulnerability_record(
                                unique_id=cve_id,
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
                        logger.error(f"Error parsing Schneider table row: {e}")
                        continue
            
            # Also look for CVE links directly
            cve_links = soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}'))
            for cve_link in cve_links:
                try:
                    cve_id = cve_link.text.strip()
                    if not cve_id or not re.match(r'CVE-\d{4}-\d{4,7}', cve_id):
                        continue
                    
                    # Get the parent container for this CVE
                    parent = cve_link.find_parent(['div', 'article', 'section', 'tr', 'td'])
                    if not parent:
                        continue
                    
                    # Extract title/description
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or cve_link
                    title = title_elem.get_text().strip() if title_elem else cve_id
                    
                    # Extract description from surrounding text
                    desc_elem = parent.find(['p', 'div', 'span'], class_=re.compile(r'description|summary|content', re.I))
                    if not desc_elem:
                        desc_text = parent.get_text()
                        description = desc_text.replace(title, '').strip()
                    else:
                        description = desc_elem.get_text().strip()
                    
                    # Extract severity
                    severity = self.extract_schneider_severity(title + " " + description)
                    
                    # Extract product information
                    product_name = self.extract_schneider_product(title, description)
                    
                    # Extract published date
                    date_elem = parent.find(['time', 'span', 'div'], class_=re.compile(r'date|published|updated', re.I))
                    published_date = datetime.now()
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
                    logger.error(f"Error parsing Schneider CVE link: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping Schneider vulnerabilities: {e}")
        
        return vulnerabilities
    
    def extract_cve_ids_from_text(self, text: str) -> List[str]:
        """Extract all CVE IDs from text"""
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        return re.findall(cve_pattern, text, re.IGNORECASE)
    
    def extract_schneider_severity(self, text: str) -> str:
        """Extract severity from Schneider text"""
        text_lower = text.lower()
        
        if 'critical' in text_lower:
            return 'Critical'
        elif 'high' in text_lower:
            return 'High'
        elif 'medium' in text_lower:
            return 'Medium'
        elif 'low' in text_lower:
            return 'Low'
        else:
            return 'Unknown'
    
    def extract_schneider_product(self, title: str, description: str) -> str:
        """Extract product name from Schneider vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Schneider Electric products
        products = [
            'ecostruxure', 'power monitoring expert', 'power operation', 'power scada',
            'modicon', 'altivar', 'telemecanique', 'schneider electric', 'saitel',
            'wonderware', 'aveva', 'clearscada', 'struxureware', 'triconex',
            'foxboro', 'modbus', 'ethernet', 'hmi', 'scada', 'plc'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Schneider Electric Product"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from Schneider text"""
        return self.extract_schneider_severity(text)
