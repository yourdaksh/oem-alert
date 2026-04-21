'use client';
/**
 * Global scan-in-progress banner.
 *
 * Primary source of truth is the ScanContext (same-tab, always accurate).
 * Falls back to localStorage (`oem-alert.scan`) so other browser tabs can
 * still see the banner while a scan is mid-flight.
 */
import { useEffect, useRef, useState } from 'react';
import { Loader2, X, CheckCircle2 } from 'lucide-react';
import { useScan } from './ScanContext';

type BannerState = {
  running: boolean;
  total: number;
  completed: number;
  failed: number;
  startedAt: number;
  lastOem?: string | null;
};

const KEY = 'oem-alert.scan';

function readBanner(): BannerState | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const s = JSON.parse(raw) as BannerState;
    if (s.running && Date.now() - (s.startedAt || 0) > 15 * 60 * 1000) {
      window.localStorage.removeItem(KEY);
      return null;
    }
    return s;
  } catch { return null; }
}

export function writeScanState(s: BannerState | null) {
  if (typeof window === 'undefined') return;
  if (!s) window.localStorage.removeItem(KEY);
  else window.localStorage.setItem(KEY, JSON.stringify(s));
  window.dispatchEvent(new CustomEvent('oem-alert-scan-change'));
}

export default function ScanBanner() {
  const { runningAll, summary, oems, startedAt } = useScan();
  const [fallback, setFallback] = useState<BannerState | null>(null);
  const [justFinished, setJustFinished] = useState<null | { ok: number; failed: number; found: number; new: number }>(null);
  const prevRunningAll = useRef(false);

  // Cross-tab fallback
  useEffect(() => {
    const sync = () => setFallback(readBanner());
    sync();
    window.addEventListener('storage', sync);
    window.addEventListener('oem-alert-scan-change', sync as EventListener);
    const id = window.setInterval(sync, 2000);
    return () => {
      window.removeEventListener('storage', sync);
      window.removeEventListener('oem-alert-scan-change', sync as EventListener);
      window.clearInterval(id);
    };
  }, []);

  // Flash "done" toast for a few seconds after a scanAll finishes
  useEffect(() => {
    if (prevRunningAll.current && !runningAll && startedAt) {
      setJustFinished({ ok: summary.ok, failed: summary.failed, found: summary.found, new: summary.new });
      const t = setTimeout(() => setJustFinished(null), 6000);
      prevRunningAll.current = runningAll;
      return () => clearTimeout(t);
    }
    prevRunningAll.current = runningAll;
  }, [runningAll, startedAt, summary.ok, summary.failed, summary.found, summary.new]);

  // Prefer in-tab context data; fall back to localStorage for cross-tab visibility
  const total = oems.filter(o => o.enabled).length;
  const completed = summary.ok;
  const failed = summary.failed;
  const running = runningAll || (fallback?.running ?? false);
  const pct = (total || fallback?.total)
    ? Math.round(((completed + failed) / (total || fallback!.total)) * 100)
    : 0;
  const label = running
    ? (fallback?.lastOem ? `Scanning ${fallback.lastOem}...` : 'Running full scan...')
    : null;

  if (running) {
    const shownTotal = total || fallback?.total || 0;
    const shownCompleted = runningAll ? completed : (fallback?.completed ?? 0);
    const shownFailed = runningAll ? failed : (fallback?.failed ?? 0);
    return (
      <div style={{
        background: 'linear-gradient(90deg, rgba(52,211,153,0.18), rgba(52,211,153,0.06))',
        border: '1px solid rgba(52,211,153,0.35)',
        borderRadius: 8,
        padding: '0.6rem 0.9rem',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        fontSize: '0.85rem',
      }}>
        <Loader2 size={14} className="animate-spin" color="var(--primary)" />
        <span style={{ color: '#d4d4d8', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
          <span style={{ color: '#71717a', marginLeft: '0.5rem' }}>
            {shownCompleted + shownFailed}/{shownTotal} · {pct}%
            {shownFailed > 0 && <span style={{ color: '#fca5a5' }}> ({shownFailed} failed)</span>}
          </span>
        </span>
      </div>
    );
  }

  if (justFinished) {
    return (
      <div style={{
        background: 'rgba(52,211,153,0.08)',
        border: '1px solid rgba(52,211,153,0.25)',
        borderRadius: 8,
        padding: '0.6rem 0.9rem',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        fontSize: '0.85rem',
      }}>
        <CheckCircle2 size={14} color="var(--primary)" />
        <span style={{ color: '#d4d4d8', flex: 1 }}>
          Scan complete · {justFinished.ok} ok
          {justFinished.failed ? <span style={{ color: '#fca5a5' }}> · {justFinished.failed} failed</span> : null}
          <span style={{ color: '#71717a' }}> · {justFinished.found} CVEs found, {justFinished.new} new</span>
        </span>
        <button onClick={() => setJustFinished(null)} aria-label="Dismiss"
          style={{ background: 'transparent', border: 'none', color: '#71717a', cursor: 'pointer', padding: 2 }}>
          <X size={14} />
        </button>
      </div>
    );
  }

  return null;
}
