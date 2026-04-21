'use client';
import { useMemo } from 'react';
import { Loader2, Zap, CheckCircle2, XCircle } from 'lucide-react';
import { useScan } from '../ScanContext';

export default function ScanPage() {
  const {
    loading, error, oems, running, runningAll, summary, lastByOem,
    scanOne, scanAll, isOwner, startedAt,
  } = useScan();

  const enabledCount = useMemo(() => oems.filter(o => o.enabled).length, [oems]);

  if (loading) {
    return <div style={{ padding: '2rem' }}><Loader2 className="animate-spin" size={20} /></div>;
  }

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

  async function handleScanAll() {
    if (runningAll) return;
    if (!confirm(
      `Run every scraper now?\n\n` +
      `${enabledCount} OEMs will run ${6} at a time. Typical full scan finishes ` +
      `in ~3-5 minutes. You can keep using the rest of the app — progress stays ` +
      `in the banner at the top.`
    )) return;
    await scanAll();
  }

  const inFlight = summary.ok + summary.failed + summary.running;
  const progressPct = runningAll && enabledCount
    ? Math.round(((summary.ok + summary.failed) / enabledCount) * 100)
    : 0;

  return (
    <div className="animate-fade-in-up">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>Manual Scan</h1>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Run scrapers on demand. Scans continue in the background — you can switch pages freely.
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
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: '1.1rem', margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Zap size={16} color="var(--primary)" /> Scan all OEMs
            </h2>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0 }}>
              Runs every enabled scraper in parallel batches. Typically 3-5 minutes.
            </p>
          </div>
          <button onClick={handleScanAll} disabled={runningAll} className="btn btn-primary"
            style={{ padding: '0.65rem 1.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {runningAll ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {runningAll ? 'Scanning...' : 'Run full scan'}
          </button>
        </div>

        {runningAll && (
          <div style={{ marginTop: '0.85rem' }}>
            <div style={{ height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                width: `${progressPct}%`, height: '100%',
                background: 'linear-gradient(90deg, var(--primary), #a7f3d0)',
                transition: 'width 0.4s ease',
              }} />
            </div>
            <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: '#a1a1aa', display: 'flex', justifyContent: 'space-between' }}>
              <span>{summary.ok + summary.failed}/{enabledCount} complete ({progressPct}%)</span>
              <span>
                {startedAt && (
                  <>elapsed {Math.round((Date.now() - startedAt) / 1000)}s</>
                )}
              </span>
            </div>
          </div>
        )}

        {inFlight > 0 && (
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
                <div style={{ minWidth: 0, flex: 1 }}>
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
                        <XCircle size={12} /> {state.error?.slice(0, 120)}
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
                  style={{ padding: '0.4rem 0.9rem', background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: 6, color: 'white', fontSize: '0.82rem', cursor: (!o.enabled || state?.status === 'running' || runningAll) ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', opacity: (!o.enabled || runningAll) ? 0.55 : 1 }}>
                  {state?.status === 'running' ? 'Scanning...' : 'Scan'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
