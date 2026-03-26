
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.vmware import VMwareScraper
from pprint import pprint

print("Starting VMware verification...")
config = {
    "name": "VMware",
    "rss_url": "https://www.vmware.com/security/advisories.xml",
    "base_url": "https://www.vmware.com"
}

try:
    scraper = VMwareScraper(config)
    vulns = scraper.run_scrape()
    print(f"Found {len(vulns)} vulnerabilities.")
    if vulns:
        pprint(vulns[0])
except Exception as e:
    print(f"Error: {e}")
