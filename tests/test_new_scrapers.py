
import sys
import os
import logging
from pprint import pprint

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers import create_scraper_manager

# Configure logging to show info
logging.basicConfig(level=logging.INFO)

def test_new_scrapers():
    manager = create_scraper_manager()
    
    new_oems = ['redhat', 'paloalto', 'fortinet', 'vmware', 'citrix']
    
    for oem in new_oems:
        print(f"\n{'='*50}")
        print(f"Testing Scraper: {oem}")
        print(f"{'='*50}")
        
        scraper = manager.get_scraper(oem)
        if not scraper:
            print(f"❌ Scraper not found or failed to initialize: {oem}")
            continue
            
        try:
            # Run scrape
            print(f"Fetching feed from: {scraper.oem_config.get('rss_url')}")
            vulnerabilities = scraper.run_scrape()
            
            if vulnerabilities:
                print(f"✅ Successfully found {len(vulnerabilities)} vulnerabilities.")
                print("\nSample Data (First Item):")
                pprint(vulnerabilities[0])
                
                # specific checks
                v = vulnerabilities[0]
                if not v.get('unique_id'):
                    print("⚠️  Warning: unique_id is missing")
                if v.get('severity_level') == 'Unknown':
                    print("⚠️  Warning: severity_level is Unknown (might need better parsing)")
                if not v.get('product_name'):
                    print("⚠️  Warning: product_name is missing")
                    
            else:
                print("⚠️  Scraper ran but returned 0 vulnerabilities (Feed might be empty or parsing failed).")
                
        except Exception as e:
            print(f"❌ Error running scraper: {e}")

if __name__ == "__main__":
    test_new_scrapers()
