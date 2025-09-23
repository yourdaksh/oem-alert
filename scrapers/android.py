"""
Android Security Bulletins scraper
Source: https://source.android.com/docs/security/bulletin/asb-overview
"""
import re
from datetime import datetime
from typing import List, Dict, Any
from scrapers.base import WebScraper
import logging

logger = logging.getLogger(__name__)


class AndroidScraper(WebScraper):
    """Scraper for Android Security Bulletins"""

    def scrape_vulnerabilities(self) -> List[Dict[str, Any]]:
        vulnerabilities: List[Dict[str, Any]] = []

        vuln_url = self.oem_config.get('vulnerability_url') or self.base_url
        soup = self.get_page(vuln_url)
        if not soup:
            return vulnerabilities

        try:
            # Find monthly bulletin links from the overview page
            monthly_links: List[str] = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = (a.get_text() or '').lower()
                if 'android security bulletin' in text or re.search(r'/security/bulletin/20\d{2}-\d{2}', href):
                    if href.startswith('/'):
                        href = 'https://source.android.com' + href
                    monthly_links.append(href)

            # Deduplicate and limit
            seen = set()
            monthly_links = [l for l in monthly_links if not (l in seen or seen.add(l))][:6]

            # Parse each monthly bulletin table
            for month_url in monthly_links:
                inner = self.get_page(month_url)
                if not inner:
                    continue
                self._parse_android_tables(inner, month_url, vulnerabilities)

            # Fallback: parse current page tables as well
            self._parse_android_tables(soup, vuln_url, vulnerabilities)

        except Exception as e:
            logger.error(f"Error scraping Android page: {e}")

        return vulnerabilities

    def _parse_android_tables(self, soup, source_url: str, out: List[Dict[str, Any]]):
        cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}', re.I)
        for table in soup.find_all('table'):
            try:
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if not cells:
                        continue
                    joined = ' '.join([c.get_text(separator=' ').strip() for c in cells])
                    cve_match = cve_pattern.search(joined)
                    if not cve_match:
                        continue
                    cve_id = cve_match.group(0)

                    severity = 'Unknown'
                    if re.search(r'critical', joined, re.I):
                        severity = 'Critical'
                    elif re.search(r'high', joined, re.I):
                        severity = 'High'
                    elif re.search(r'medium', joined, re.I):
                        severity = 'Medium'
                    elif re.search(r'low', joined, re.I):
                        severity = 'Low'

                    cvss_score = self.extract_cvss_score(joined)

                    published_date = datetime.now()
                    header_date = soup.find(['time'])
                    if header_date:
                        dt_text = header_date.get('datetime') or header_date.get_text()
                        parsed = self.parse_date(dt_text)
                        if parsed:
                            published_date = parsed

                    out.append(self.create_vulnerability_record(
                        unique_id=cve_id,
                        product_name='Android',
                        product_version=None,
                        severity_level=severity,
                        vulnerability_description=joined[:500],
                        mitigation_strategy=None,
                        published_date=published_date,
                        source_url=source_url,
                        cvss_score=cvss_score,
                    ))
            except Exception as e:
                logger.error(f"Error parsing Android table: {e}")

        # Fallback: text-based scan
        for a in soup.find_all('a', href=re.compile(r'CVE-\d{4}-\d{4,7}', re.I)):
            try:
                cve_id = re.search(r'CVE-\d{4}-\d{4,7}', a.get('href') or a.text, re.I)
                if not cve_id:
                    continue
                cve = cve_id.group(0)
                parent = a.find_parent('tr') or a.find_parent(['div', 'li', 'section']) or soup
                text = parent.get_text(separator=' ').strip() if parent else a.text
                severity = self.extract_severity_from_text(text)
                cvss_score = self.extract_cvss_score(text)
                published_date = datetime.now()

                out.append(self.create_vulnerability_record(
                    unique_id=cve,
                    product_name='Android',
                    product_version=None,
                    severity_level=severity,
                    vulnerability_description=text[:500],
                    mitigation_strategy=None,
                    published_date=published_date,
                    source_url=a.get('href'),
                    cvss_score=cvss_score,
                ))
            except Exception as e:
                logger.error(f"Error parsing Android fallback link: {e}")


