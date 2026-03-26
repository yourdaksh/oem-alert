
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.citrix import CitrixScraper
from pprint import pprint

print("Starting Citrix verification...")
config = {
    "name": "Citrix",
    "rss_url": "https://support.citrix.com/feed/products/all/securitybulletins.rss",
    "base_url": "https://support.citrix.com"
}

try:
    scraper = CitrixScraper(config)
    vulns = scraper.run_scrape()
    print(f"Found {len(vulns)} vulnerabilities.")
    if vulns:
        pprint(vulns[0])
except Exception as e:
    print(f"Error: {e}")
