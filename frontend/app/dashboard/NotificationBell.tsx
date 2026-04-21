'use client';
/**
 * Header notification popover.
 *
 * Surfaces three things Owners want at a glance:
 *   - Current scan status (from ScanContext so it reflects in-flight work)
 *   - Count of Critical CVEs known to the org
 *   - A shortcut to the Alerts config in Settings
 *
 * Deliberately lightweight — a full bell-dropdown inbox isn't in scope,
 * but this turns the bell from a static icon into something that answers
 * "is anything wrong right now?" in one glance.
 */
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { Bell, Loader2, AlertTriangle, Mail, Zap, X } from 'lucide-react';
import { useScan } from './ScanContext';
import { getSupabase, API_URL } from '../../lib/supabase';

export default function NotificationBell() {
  const { runningAll, summary, oems } = useScan();
  const [open, setOpen] = useState(false);
  const [criticalCount, setCriticalCount] = useState<number | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  // Load the critical count once + refresh whenever a scan finishes so the
  // count stays in sync with what the dashboard shows.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        if (!data.session) return;
        const headers = { Authorization: `Bearer ${data.session.access_token}` };
        const res = await fetch(`${API_URL}/vulnerabilities/?limit=2500`, { headers });
        if (!res.ok) return;
        const list = await res.json();
        if (cancelled) return;
        const crit = list.filter((v: any) => (v.severity_level || '').toLowerCase() === 'critical').length;
        setCriticalCount(crit);
      } catch { /* silent; bell still works */ }
    })();
    return () => { cancelled = true; };
  }, [runningAll]);

  // Close on outside click / Escape
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!panelRef.current || !buttonRef.current) return;
      const t = e.target as Node;
      if (panelRef.current.contains(t) || buttonRef.current.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const total = oems.filter(o => o.enabled).length;
  const dot = runningAll || (criticalCount && criticalCount > 0);

  return (
    <div style={{ position: 'relative' }}>
      <button
        ref={buttonRef}
        onClick={() => setOpen(o => !o)}
        aria-label="Notifications"
        aria-expanded={open}
        style={{
          background: 'transparent', border: 'none', color: '#a1a1aa',
          cursor: 'pointer', padding: 6, display: 'inline-flex', alignItems: 'center',
          position: 'relative',
        }}>
        <Bell size={20} />
        {dot && (
          <span style={{
            position: 'absolute', top: 2, right: 2, width: 8, height: 8,
            background: runningAll ? 'var(--primary)' : 'var(--danger)',
            borderRadius: '50%', boxShadow: '0 0 0 2px var(--background)',
          }} />
        )}
      </button>

      {open && (
        <div ref={panelRef}
          style={{
            position: 'absolute', top: 'calc(100% + 8px)', right: 0, width: 320,
            background: 'rgba(15,17,22,0.98)', backdropFilter: 'blur(20px)',
            border: '1px solid var(--surface-border)', borderRadius: 10,
            boxShadow: '0 20px 40px rgba(0,0,0,0.45)', zIndex: 80,
            overflow: 'hidden',
          }}>
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#d4d4d8' }}>Notifications</span>
            <button onClick={() => setOpen(false)} aria-label="Close"
              style={{ background: 'transparent', border: 'none', color: '#71717a', cursor: 'pointer', padding: 2 }}>
              <X size={14} />
            </button>
          </div>

          <div style={{ padding: '0.75rem' }}>
            {/* Scan status */}
            <div style={{ padding: '0.65rem 0.8rem', borderRadius: 8, background: runningAll ? 'rgba(52,211,153,0.08)' : 'var(--surface)', border: '1px solid var(--surface-border)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              {runningAll
                ? <Loader2 size={14} className="animate-spin" color="var(--primary)" />
                : <Zap size={14} color="#71717a" />}
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontSize: '0.8rem', color: '#d4d4d8' }}>
                  {runningAll ? 'Manual scan in progress' : 'No scans running'}
                </div>
                {runningAll && total > 0 && (
                  <div style={{ fontSize: '0.72rem', color: '#71717a' }}>
                    {summary.ok + summary.failed}/{total} complete
                    {summary.failed > 0 && <span style={{ color: '#fca5a5' }}> · {summary.failed} failed</span>}
                  </div>
                )}
              </div>
            </div>

            {/* Critical CVEs */}
            <Link href="/dashboard/vulnerabilities" onClick={() => setOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.6rem',
                padding: '0.65rem 0.8rem', borderRadius: 8,
                background: (criticalCount ?? 0) > 0 ? 'rgba(239,68,68,0.08)' : 'var(--surface)',
                border: '1px solid var(--surface-border)',
                marginBottom: '0.5rem', textDecoration: 'none', color: 'inherit',
              }}>
              <AlertTriangle size={14} color={(criticalCount ?? 0) > 0 ? 'var(--danger)' : '#71717a'} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.8rem', color: '#d4d4d8' }}>
                  {criticalCount === null
                    ? 'Loading critical CVEs...'
                    : criticalCount === 0
                      ? 'No critical CVEs'
                      : `${criticalCount} critical CVE${criticalCount === 1 ? '' : 's'}`}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#71717a' }}>
                  Open Vulnerabilities →
                </div>
              </div>
            </Link>

            {/* Configure alerts */}
            <Link href="/dashboard/settings#alerts" onClick={() => setOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.6rem',
                padding: '0.65rem 0.8rem', borderRadius: 8,
                background: 'var(--surface)', border: '1px solid var(--surface-border)',
                textDecoration: 'none', color: 'inherit',
              }}>
              <Mail size={14} color="#a1a1aa" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.8rem', color: '#d4d4d8' }}>Configure email & Slack alerts</div>
                <div style={{ fontSize: '0.72rem', color: '#71717a' }}>Settings → Alerts</div>
              </div>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
