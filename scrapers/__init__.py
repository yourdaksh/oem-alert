"""
Scraper registry and initialization
"""
from typing import Dict, List, Any, Type
from scrapers.base import BaseScraper
from scrapers.intel import IntelScraper
from scrapers.oracle import OracleScraper
from scrapers.ubuntu import UbuntuScraper
from scrapers.android import AndroidScraper
from scrapers.schneider import SchneiderScraper
from scrapers.cisco import CiscoScraper
from scrapers.debian import DebianScraper
from config import get_all_oems, get_enabled_oems
import logging

logger = logging.getLogger(__name__)

# Registry of available scrapers (active only)
SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    'intel': IntelScraper,
    'oracle': OracleScraper,
    'ubuntu': UbuntuScraper,
    'android': AndroidScraper,
    'schneider': SchneiderScraper,
    'cisco': CiscoScraper,
    'debian': DebianScraper,
}

class ScraperManager:
    """Manages all OEM scrapers"""
    
    def __init__(self):
        self.scrapers: Dict[str, BaseScraper] = {}
        self.oems_config = get_all_oems()
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize all enabled scrapers"""
        enabled_oems = get_enabled_oems()
        
        for oem_id in enabled_oems:
            if oem_id in SCRAPER_REGISTRY:
                oem_config = self.oems_config.get(oem_id, {})
                scraper_class = SCRAPER_REGISTRY[oem_id]
                
                try:
                    scraper = scraper_class(oem_config)
                    self.scrapers[oem_id] = scraper
                    logger.info(f"Initialized scraper for {oem_config.get('name', oem_id)}")
                except Exception as e:
                    logger.error(f"Failed to initialize scraper for {oem_id}: {e}")
            else:
                logger.warning(f"No scraper available for {oem_id}")
    
    def get_scraper(self, oem_id: str) -> BaseScraper:
        """Get a specific scraper by OEM ID"""
        return self.scrapers.get(oem_id)
    
    def get_all_scrapers(self) -> Dict[str, BaseScraper]:
        """Get all initialized scrapers"""
        return self.scrapers
    
    def run_scraper(self, oem_id: str) -> List[Dict[str, Any]]:
        """Run a specific scraper"""
        scraper = self.get_scraper(oem_id)
        if not scraper:
            logger.error(f"No scraper found for {oem_id}")
            return []
        
        try:
            return scraper.run_scrape()
        except Exception as e:
            logger.error(f"Error running scraper for {oem_id}: {e}")
            return []
    
    def run_all_scrapers(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run all enabled scrapers"""
        results = {}
        
        for oem_id, scraper in self.scrapers.items():
            logger.info(f"Running scraper for {oem_id}")
            try:
                vulnerabilities = scraper.run_scrape()
                results[oem_id] = vulnerabilities
                logger.info(f"Found {len(vulnerabilities)} vulnerabilities for {oem_id}")
            except Exception as e:
                logger.error(f"Error running scraper for {oem_id}: {e}")
                results[oem_id] = []
        
        return results
    
    def get_scraper_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all scrapers"""
        status = {}
        
        for oem_id, scraper in self.scrapers.items():
            oem_config = self.oems_config.get(oem_id, {})
            status[oem_id] = {
                'name': oem_config.get('name', oem_id),
                'enabled': oem_config.get('enabled', True),
                'scan_interval_hours': oem_config.get('scan_interval_hours', 24),
                'base_url': oem_config.get('base_url', ''),
                'description': oem_config.get('description', ''),
                'scraper_class': scraper.__class__.__name__
            }
        
        return status

def create_scraper_manager() -> ScraperManager:
    """Create and return a new ScraperManager instance"""
    return ScraperManager()

# Convenience function for getting all available OEMs
def get_available_oems() -> List[str]:
    """Get list of all available OEMs (enabled and disabled)"""
    return list(get_all_oems().keys())

# Convenience function for getting enabled OEMs
def get_enabled_oem_list() -> List[str]:
    """Get list of enabled OEMs"""
    return get_enabled_oems()