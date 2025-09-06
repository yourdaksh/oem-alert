"""
Ubuntu Security Notices scraper
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from scrapers.base import RSSScraper
import logging

logger = logging.getLogger(__name__)

class UbuntuScraper(RSSScraper):
    """Scraper for Ubuntu Security Notices"""
    
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape Ubuntu vulnerabilities"""
        vulnerabilities = []
        
        # Try RSS feed first
        rss_url = self.oem_config.get('rss_url')
        if rss_url:
            vulnerabilities.extend(self.parse_rss_feed(rss_url))
        
        # Also scrape the main security notices page
        vuln_url = self.oem_config.get('vulnerability_url')
        if vuln_url:
            soup = self.get_page(vuln_url)
            if soup:
                vulnerabilities.extend(self.parse_ubuntu_page(soup))
        
        return vulnerabilities
    
    def parse_ubuntu_page(self, soup) -> List[Dict[str, Any]]:
        """Parse Ubuntu security notices page"""
        vulnerabilities = []
        
        try:
            # Look for security notice entries
            notice_sections = soup.find_all('div', class_=re.compile(r'notice|security|advisory', re.I))
            
            for section in notice_sections:
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
                        severity = self.extract_ubuntu_severity(parent)
                        
                        # Extract product information
                        product_name = self.extract_ubuntu_product(title, description)
                        
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
                    logger.error(f"Error parsing Ubuntu notice section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Ubuntu page: {e}")
        
        return vulnerabilities
    
    def extract_ubuntu_severity(self, element) -> str:
        """Extract severity from Ubuntu vulnerability element"""
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
    
    def extract_ubuntu_product(self, title: str, description: str) -> str:
        """Extract product name from Ubuntu vulnerability"""
        text = (title + " " + description).lower()
        
        # Common Ubuntu/Linux products
        products = [
            'ubuntu', 'ubuntu server', 'ubuntu desktop', 'ubuntu core',
            'kernel', 'linux kernel', 'systemd', 'glibc', 'openssl',
            'apache', 'nginx', 'mysql', 'postgresql', 'php',
            'python', 'ruby', 'nodejs', 'docker', 'kubernetes',
            'snap', 'snapcraft', 'cloud-init', 'netplan',
            'firefox', 'chromium', 'thunderbird', 'libreoffice',
            'gcc', 'g++', 'clang', 'cmake', 'make',
            'vim', 'emacs', 'nano', 'bash', 'zsh',
            'ssh', 'openssh', 'curl', 'wget', 'git'
        ]
        
        for product in products:
            if product in text:
                return product.title()
        
        # Try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])
        
        return "Ubuntu Package"
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from Ubuntu text"""
        return self.extract_ubuntu_severity(type('obj', (object,), {'get_text': lambda self: text})())
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from Ubuntu RSS item"""
        return self.extract_ubuntu_product(title, description)
