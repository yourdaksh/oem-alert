-- Per-org list of OEMs the tenant has actually pulled scans for.
-- Without this, a new org with enabled_oems = "ALL" sees the entire shared
-- vulnerability pool the moment last_scan_at is flipped by a single OEM scan.
-- We use it at read time so /vulnerabilities/ returns only rows for OEMs this
-- org has scraped at least once, not every CVE in the global pool.

ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS scanned_oems TEXT;

COMMENT ON COLUMN organizations.scanned_oems IS
  'Comma-separated display names of OEMs this org has successfully scanned. Drives vulnerabilities feed filtering.';
