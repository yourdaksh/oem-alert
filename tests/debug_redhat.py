
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.redhat import RedHatScraper
from pprint import pprint

print("Starting RedHat debug test...")
config = {
    "name": "Red Hat",
    "rss_url": "https://access.redhat.com/rss/content/security-advisories",
    "base_url": "https://access.redhat.com"
}
try:
    scraper = RedHatScraper(config)
    print("Scraper initialized.")
    vulns = scraper.run_scrape()
    print(f"Found {len(vulns)} vulnerabilities.")
    if vulns:
        pprint(vulns[0])
except Exception as e:
    print(f"Error: {e}")
