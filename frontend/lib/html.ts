/**
 * Strip HTML tags + decode entities from scraped text.
 *
 * Scrapers pull vendor advisory pages, often grabbing `<div>` fragments with
 * image tags, anchors, and long `<p>` blocks. Rendering that raw fills the
 * UI with unreadable markup. Doing this at render time (rather than on
 * ingest) avoids a DB migration and lets us iterate on the sanitizer
 * without rescraping.
 */
export function stripHtml(raw: string | null | undefined): string {
  if (!raw) return '';
  if (typeof window === 'undefined') return raw.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  const doc = new DOMParser().parseFromString(raw, 'text/html');
  const text = doc.body?.textContent || '';
  return text.replace(/\s+/g, ' ').trim();
}

export function extractCveIds(text: string, limit = 5): string[] {
  const matches = text.match(/CVE-\d{4}-\d{4,7}/g) || [];
  const unique = Array.from(new Set(matches));
  return unique.slice(0, limit);
}
