"""
Base scraper class and utilities for vulnerability scraping
"""
import requests
from bs4 import BeautifulSoup
try:
    import selenium
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    webdriver = None
    Options = None
    By = None
    WebDriverWait = None
    EC = None
    HAS_SELENIUM = False
except Exception as e:
    # Catch other initialization errors
    logging.warning(f"Selenium import failed: {e}")
    HAS_SELENIUM = False
from datetime import datetime, timedelta
import re
import time
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all OEM scrapers"""
    
    def __init__(self, oem_config: Dict[str, Any]):
        self.oem_config = oem_config
        self.oem_name = oem_config.get('name', 'Unknown')
        self.base_url = oem_config.get('base_url', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        
    def __del__(self):
        """Cleanup selenium driver if it exists"""
        if self.driver:
            self.driver.quit()
    
    def setup_selenium(self, headless: bool = True):
        """Setup selenium webdriver"""
        if not HAS_SELENIUM:
            logger.warning("Selenium not available; cannot setup webdriver")
            return None
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return None
    
    def get_page(self, url: str, use_selenium: bool = False, wait_for_element: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Get page content using requests or selenium"""
        try:
            if use_selenium:
                if not self.driver:
                    self.setup_selenium()
                
                if not self.driver:
                    return None
                
                self.driver.get(url)
                
                if wait_for_element:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                
                # Wait a bit for dynamic content to load
                time.sleep(2)
                
                html = self.driver.page_source
                return BeautifulSoup(html, 'html.parser')
            else:
                response = self.session.get(url, timeout=15)
                try:
                    response.raise_for_status()
                except requests.HTTPError as http_err:
                    status = getattr(response, 'status_code', None)
                    # Fallback to Selenium for common block statuses
                    if status in (403, 429) and HAS_SELENIUM:
                        logger.warning(f"HTTP {status} for {url}; retrying with Selenium headless")
                        return self.get_page(url, use_selenium=True, wait_for_element=wait_for_element)
                    raise
                return BeautifulSoup(response.content, 'html.parser')
                
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def extract_cve_id(self, text: str) -> Optional[str]:
        """Extract CVE ID from text"""
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        match = re.search(cve_pattern, text, re.IGNORECASE)
        return match.group() if match else None
    
    def extract_cvss_score(self, text: str) -> Optional[str]:
        """Extract CVSS score from text"""
        cvss_patterns = [
            r'CVSS:3\.\d/\d+\.\d',
            r'CVSS\s+Score:\s*(\d+\.\d+)',
            r'Score:\s*(\d+\.\d+)'
        ]
        
        for pattern in cvss_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if len(match.groups()) > 0 else match.group()
        
        return None
    
    def normalize_severity(self, severity: str) -> str:
        """Normalize severity levels"""
        severity_lower = severity.lower().strip()
        
        if any(word in severity_lower for word in ['critical', 'cve', 'urgent']):
            return 'Critical'
        elif any(word in severity_lower for word in ['high', 'important', 'severe']):
            return 'High'
        elif any(word in severity_lower for word in ['medium', 'moderate', 'normal']):
            return 'Medium'
        elif any(word in severity_lower for word in ['low', 'minor', 'informational']):
            return 'Low'
        else:
            return 'Unknown'
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        date_patterns = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for pattern in date_patterns:
            try:
                return datetime.strptime(date_str.strip(), pattern)
            except ValueError:
                continue
        
        # Try to extract date from text
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
        if date_match:
            try:
                return datetime.strptime(date_match.group(), '%Y-%m-%d')
            except ValueError:
                pass
        
        return None

    def extract_severity_from_text(self, text: str) -> str:
        """Default severity extractor based on keyword mapping"""
        return self.normalize_severity(text or "")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
    
    def create_vulnerability_record(self, 
                                  unique_id: str,
                                  product_name: str,
                                  product_version: Optional[str],
                                  severity_level: str,
                                  vulnerability_description: str,
                                  mitigation_strategy: Optional[str],
                                  published_date: datetime,
                                  source_url: Optional[str] = None,
                                  cvss_score: Optional[str] = None,
                                  affected_versions: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized vulnerability record"""
        return {
            'unique_id': unique_id,
            'product_name': self.clean_text(product_name),
            'product_version': self.clean_text(product_version) if product_version else None,
            'oem_name': self.oem_name,
            'severity_level': self.normalize_severity(severity_level),
            'vulnerability_description': self.clean_text(vulnerability_description),
            'mitigation_strategy': self.clean_text(mitigation_strategy) if mitigation_strategy else None,
            'published_date': published_date,
            'source_url': source_url,
            'cvss_score': cvss_score,
            'affected_versions': affected_versions
        }
    
    @abstractmethod
    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scrape vulnerabilities from the OEM website - must be implemented by subclasses"""
        pass
    
    def run_scrape(self) -> List[Dict[str, Any]]:
        """Run the scraping process with error handling"""
        try:
            logger.info(f"Starting scrape for {self.oem_name}")
            vulnerabilities = self.scrape_vulnerabilities()
            logger.info(f"Found {len(vulnerabilities)} vulnerabilities for {self.oem_name}")
            return vulnerabilities
        except Exception as e:
            logger.error(f"Error scraping {self.oem_name}: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

class RSSScraper(BaseScraper):
    """Base class for scrapers that use RSS feeds"""
    
    def parse_rss_feed(self, rss_url: str) -> List[Dict[str, Any]]:
        """Parse RSS feed for vulnerabilities"""
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
                    
                    # Extract CVE ID
                    cve_id = self.extract_cve_id(title + " " + description)
                    if not cve_id:
                        cve_id = f"{self.oem_name.lower()}-{hash(title)}"
                    
                    # Parse published date
                    published_date = self.parse_date(pub_date)
                    if not published_date:
                        published_date = datetime.now()
                    
                    # Extract severity from title/description
                    severity = self.extract_severity_from_text(title + " " + description)
                    
                    # Extract product name
                    product_name = self.extract_product_name(title, description)
                    
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
                    logger.error(f"Error parsing RSS item: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {rss_url}: {e}")
        
        return vulnerabilities
    
    def extract_severity_from_text(self, text: str) -> str:
        """Extract severity from text - override in subclasses for specific patterns"""
        return self.normalize_severity(text)
    
    def extract_product_name(self, title: str, description: str) -> str:
        """Extract product name from title/description - override in subclasses"""
        # Default implementation - try to extract from title
        words = title.split()
        if len(words) > 1:
            return " ".join(words[:2])  # Take first two words as product name
        return title

class WebScraper(BaseScraper):
    """Base class for scrapers that parse HTML pages"""
    
    def find_vulnerability_elements(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Find vulnerability elements on the page - override in subclasses"""
        # Default implementation - look for common patterns
        elements = []
        
        # Look for tables with vulnerability data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:  # Has header and data rows
                elements.extend(rows[1:])  # Skip header row
        
        # Look for divs with vulnerability information
        vuln_divs = soup.find_all('div', class_=re.compile(r'vuln|security|advisory', re.I))
        elements.extend(vuln_divs)
        
        return elements
    
    def parse_vulnerability_element(self, element: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse a vulnerability element - override in subclasses"""
        # Default implementation - extract basic information
        text = element.get_text()
        
        # Extract CVE ID
        cve_id = self.extract_cve_id(text)
        if not cve_id:
            return None
        
        # Extract other information
        severity = self.extract_severity_from_text(text)
        cvss_score = self.extract_cvss_score(text)
        
        # Try to find links
        links = element.find_all('a')
        source_url = links[0]['href'] if links else None
        
        vuln_record = self.create_vulnerability_record(
            unique_id=cve_id,
            product_name="Unknown Product",
            product_version=None,
            severity_level=severity,
            vulnerability_description=text[:500],  # Truncate long descriptions
            mitigation_strategy=None,
            published_date=datetime.now(),
            source_url=source_url,
            cvss_score=cvss_score
        )
        
        return vuln_record
