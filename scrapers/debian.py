from scrapers.base import RSSScraper
class DebianScraper(RSSScraper):
    def scrape_vulnerabilities(self):
        rss_url = self.oem_config.get('rss_url')
        return self.parse_rss_feed(rss_url) if rss_url else []
