'use client';
import { useEffect, useMemo, useState } from 'react';
import { Loader2, Zap, CheckCircle2, XCircle, ExternalLink } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type OemEntry = { id: string; name: string; description: string; enabled: boolean };
type ScanLog = {
  oem_name: string; scan_type: string; status: string;
  vulnerabilities_found: number; new_vulnerabilities: number;
  error_message: string | null; scan_date: string;
};
type RunResult = { oem: string; status: 'running' | 'ok' | 'error'; found?: number; new?: number; error?: string };

export default function ScanPage() {
  const [oems, setOems] = useState<OemEntry[]>([]);
  const [logs, setLogs] = useState<ScanLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<Record<string, RunResult>>({});
  const [runningAll, setRunningAll] = useState(false);
  const [role, setRole] = useState<string>('');

  async function authHeaders(): Promise<Record<string, string>> {
    const { data } = await getSupabase().auth.getSession();
    return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
  }

  async function load() {
    setError(null);
    try {
      const headers = await authHeaders();
      const [oemsRes, logsRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/scrapers/oems`, { headers }),
        fetch(`${API_URL}/scrapers/status?limit=40`, { headers }),
        fetch(`${API_URL}/organizations/members`, { headers }),
      ]);
      if (!oemsRes.ok) throw new Error((await oemsRes.json()).detail || 'Not allowed');
      setOems(await oemsRes.json());
      if (logsRes.ok) setLogs(await logsRes.json());
      if (membersRes.ok) {
        const m = await membersRes.json();
        const { data: u } = await getSupabase().auth.getUser();
        setRole(m.find((x: any) => x.id === u.user?.id)?.role || '');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function scanOne(oemId: string) {
    setRunning(p => ({ ...p, [oemId]: { oem: oemId, status: 'running' } }));
    // 90s cap so a hung scraper can't leave the UI in "Scanning..." forever.
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 90_000);
    try {
      const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/scrapers/run-one/${oemId}`, {
        method: 'POST', headers, signal: controller.signal,
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.detail || `Scrape failed (${res.status})`);
      setRunning(p => ({ ...p, [oemId]: { oem: oemId, status: 'ok', found: payload.found, new: payload.new } }));
      await load(); // refresh scan_logs
    } catch (e: any) {
      const msg = e.name === 'AbortError' ? 'Timed out after 90s' : e.message;
      setRunning(p => ({ ...p, [oemId]: { oem: oemId, status: 'error', error: msg } }));
    } finally {
      clearTimeout(timer);
    }
  }

  async function scanAll() {
    if (!confirm('Run every scraper sequentially? Takes ~1-2 minutes.')) return;
    setRunningAll(true);
    setRunning({});
    for (const o of oems.filter(x => x.enabled)) {
      await scanOne(o.id);
    }
    setRunningAll(false);
  }

  const lastByOem = useMemo(() => {
    const m: Record<string, ScanLog> = {};
    for (const l of logs) {
      const k = l.oem_name.toLowerCase();
      if (!m[k]) m[k] = l;
    }
    return m;
  }, [logs]);

  const summary = useMemo(() => {
    const totals = Object.values(running).reduce(
      (acc, r) => {
        if (r.status === 'ok') {
          acc.found += r.found || 0;
          acc.new += r.new || 0;
          acc.ok += 1;
        } else if (r.status === 'error') {
          acc.failed += 1;
        } else if (r.status === 'running') {
          acc.running += 1;
        }
        return acc;
      },
      { ok: 0, failed: 0, running: 0, found: 0, new: 0 }
    );
    return totals;
  }, [running]);

  const isOwner = role === 'Owner' || role === 'Admin';

  if (loading) return <div style={{ padding: '2rem' }}><Loader2 className="animate-spin" size={20} /></div>;

  if (!isOwner) {
    return (
      <div className="animate-fade-in-up">
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Manual Scan</h1>
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: '#a1a1aa' }}>Only Owners and Admins can trigger manual scans.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in-up">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>Manual Scan</h1>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Run scrapers on demand. Automatic scans happen every {/* interval */} on your Settings schedule.
        </p>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {/* Full scan hero */}
      <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Zap size={16} color="var(--primary)" /> Scan all OEMs
            </h2>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0 }}>
              Runs every enabled scraper in sequence. Expect 1-2 minutes.
            </p>
          </div>
          <button onClick={scanAll} disabled={runningAll} className="btn btn-primary"
            style={{ padding: '0.65rem 1.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {runningAll ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {runningAll ? 'Running full scan...' : 'Run full scan'}
          </button>
        </div>
        {(summary.ok || summary.failed || summary.running) > 0 && (
          <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.9rem', background: 'var(--surface)', borderRadius: 6, fontSize: '0.8rem', color: '#a1a1aa' }}>
            {summary.running > 0 && <span style={{ color: 'var(--warning)' }}>{summary.running} running · </span>}
            <span style={{ color: 'var(--accent)' }}>{summary.ok} succeeded</span>
            {summary.failed > 0 && <span style={{ color: '#fca5a5' }}> · {summary.failed} failed</span>}
            <span> · {summary.found} CVEs found, {summary.new} new</span>
          </div>
        )}
      </div>

      {/* Per-OEM grid */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)' }}>
          <h2 style={{ fontSize: '1.05rem', margin: 0 }}>Scan individual OEMs ({oems.length})</h2>
        </div>
        <div>
          {oems.map(o => {
            const state = running[o.id];
            const last = lastByOem[o.id];
            return (
              <div key={o.id} className="scan-row" style={{ padding: '0.85rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.15rem' }}>
                    <span style={{ fontWeight: 500 }}>{o.name}</span>
                    {!o.enabled && (
                      <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', background: 'var(--surface-hover)', borderRadius: 3, color: '#71717a' }}>disabled</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#71717a' }}>
                    {state?.status === 'ok' && (
                      <span style={{ color: 'var(--accent)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                        <CheckCircle2 size={12} /> {state.found} found, {state.new} new · just now
                      </span>
                    )}
                    {state?.status === 'error' && (
                      <span style={{ color: '#fca5a5', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                        <XCircle size={12} /> {state.error?.slice(0, 80)}
                      </span>
                    )}
                    {state?.status === 'running' && (
                      <span style={{ color: 'var(--warning)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Loader2 size={12} className="animate-spin" /> scraping...
                      </span>
                    )}
                    {!state && last && (
                      <span>
                        last {last.status}: {last.vulnerabilities_found} found
                        {last.new_vulnerabilities ? `, ${last.new_vulnerabilities} new` : ''}
                        {' · '}{new Date(last.scan_date).toLocaleString()}
                      </span>
                    )}
                    {!state && !last && <span>never scanned</span>}
                  </div>
                </div>
                <button onClick={() => scanOne(o.id)} disabled={!o.enabled || state?.status === 'running' || runningAll}
                  style={{ padding: '0.4rem 0.9rem', background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: 6, color: 'white', fontSize: '0.82rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  {state?.status === 'running' ? 'Scanning...' : `Scan ${o.name}`}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
