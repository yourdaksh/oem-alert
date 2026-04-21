'use client';
import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, ExternalLink, Loader2, UserPlus, Search as SearchIcon, CheckCircle2, RefreshCw, BarChart3 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';
import { stripHtml, extractCveIds } from '../../../lib/html';

type Vuln = {
  id: string;
  unique_id: string;
  product_name: string;
  oem_name: string;
  severity_level: string;
  published_date: string;
  vulnerability_description: string;
  mitigation_strategy: string | null;
  source_url: string | null;
  cvss_score: string | null;
  affected_versions: string | null;
};

type Member = { id: string; email: string; full_name: string | null; role: string };

const SEVERITY_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, moderate: 2, low: 3, unknown: 4 };
const SEVERITY_COLORS: Record<string, { bg: string; fg: string }> = {
  critical: { bg: 'rgba(239,68,68,0.15)', fg: '#fca5a5' },
  high: { bg: 'rgba(249,115,22,0.15)', fg: '#fdba74' },
  medium: { bg: 'rgba(234,179,8,0.15)', fg: '#fde68a' },
  moderate: { bg: 'rgba(234,179,8,0.15)', fg: '#fde68a' },
  low: { bg: 'rgba(34,197,94,0.15)', fg: '#86efac' },
  unknown: { bg: 'rgba(161,161,170,0.15)', fg: '#d4d4d8' },
};

function sevStyle(s: string | null | undefined) {
  return SEVERITY_COLORS[(s || 'unknown').toLowerCase()] || SEVERITY_COLORS.unknown;
}

function SkeletonRow() {
  return (
    <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <div style={{ width: 70, height: 20, background: 'var(--surface-hover)', borderRadius: 4, animation: 'pulse 1.5s infinite' }} />
      <div style={{ width: 140, height: 16, background: 'var(--surface-hover)', borderRadius: 4 }} />
      <div style={{ flex: 1, height: 14, background: 'var(--surface-hover)', borderRadius: 4, opacity: 0.6 }} />
    </div>
  );
}

export default function VulnerabilitiesPage() {
  const [items, setItems] = useState<Vuln[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [oemFilter, setOemFilter] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('all');
  const [assigning, setAssigning] = useState<string | null>(null); // vuln.id being assigned
  const [assignTo, setAssignTo] = useState<string>('');
  const [assignBusy, setAssignBusy] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [role, setRole] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        const token = data.session?.access_token;
        if (!token) throw new Error('Not signed in');
        const headers = { Authorization: `Bearer ${token}` };
        const [vRes, mRes] = await Promise.all([
          fetch(`${API_URL}/vulnerabilities/?limit=500`, { headers }),
          fetch(`${API_URL}/organizations/members`, { headers }),
        ]);
        if (!vRes.ok) throw new Error((await vRes.json()).detail || 'Failed to load vulnerabilities');
        setItems(await vRes.json());
        if (mRes.ok) {
          const ml: Member[] = await mRes.json();
          setMembers(ml);
          const { data: user } = await getSupabase().auth.getUser();
          const me = ml.find(m => m.id === user.user?.id);
          setRole(me?.role || '');
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const oems = useMemo(() => Array.from(new Set(items.map(v => v.oem_name))).sort(), [items]);

  const summary = useMemo(() => {
    const byOem: Record<string, { total: number; critical: number; high: number; medium: number; low: number }> = {};
    const bySev: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 };
    for (const v of items) {
      const o = v.oem_name || 'Unknown';
      const s = (v.severity_level || 'unknown').toLowerCase();
      const sKey = s === 'moderate' ? 'medium' : s;
      byOem[o] = byOem[o] || { total: 0, critical: 0, high: 0, medium: 0, low: 0 };
      byOem[o].total += 1;
      if (sKey in byOem[o]) (byOem[o] as any)[sKey] += 1;
      bySev[sKey in bySev ? sKey : 'unknown'] = (bySev[sKey in bySev ? sKey : 'unknown'] || 0) + 1;
    }
    const ordered = Object.entries(byOem).sort((a, b) => b[1].total - a[1].total);
    return { byOem: ordered, bySev, total: items.length };
  }, [items]);

  const isOwner = role === 'Owner' || role === 'Admin';

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const cutoff = (() => {
      if (timeRange === 'all') return null;
      const days: Record<string, number> = { '24h': 1, '7d': 7, '30d': 30, '90d': 90 };
      const n = days[timeRange];
      if (!n) return null;
      const d = new Date();
      d.setDate(d.getDate() - n);
      return d.toISOString();
    })();
    return items
      .filter(v => severityFilter === 'all' || (v.severity_level || '').toLowerCase() === severityFilter)
      .filter(v => oemFilter === 'all' || v.oem_name === oemFilter)
      .filter(v => !cutoff || (v.published_date || '') >= cutoff)
      .filter(v => !q ||
        v.unique_id.toLowerCase().includes(q) ||
        (v.product_name || '').toLowerCase().includes(q) ||
        stripHtml(v.vulnerability_description).toLowerCase().includes(q)
      )
      .sort((a, b) => {
        const ra = SEVERITY_RANK[(a.severity_level || 'unknown').toLowerCase()] ?? 4;
        const rb = SEVERITY_RANK[(b.severity_level || 'unknown').toLowerCase()] ?? 4;
        if (ra !== rb) return ra - rb;
        return (b.published_date || '').localeCompare(a.published_date || '');
      });
  }, [items, query, severityFilter, oemFilter, timeRange]);

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  async function runScanNow() {
    if (!confirm('Queue a manual scan for your organization? It runs on the background scheduler within a few minutes.')) return;
    setScanning(true);
    try {
      const { data } = await getSupabase().auth.getSession();
      const headers = { Authorization: `Bearer ${data.session!.access_token}`, 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/scrapers/run`, { method: 'POST', headers });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.detail || 'Failed to queue scan');
      setFlash(payload.message || 'Scan queued.');
      setTimeout(() => setFlash(null), 3500);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  }

  async function submitAssign(vulnId: string) {
    if (!assignTo) return;
    setAssignBusy(true);
    try {
      const { data } = await getSupabase().auth.getSession();
      const headers = { Authorization: `Bearer ${data.session!.access_token}`, 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/tasks/`, {
        method: 'POST', headers,
        body: JSON.stringify({ vulnerability_id: vulnId, assigned_to_id: assignTo }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to assign');
      setFlash('Task created — check My Tasks');
      setTimeout(() => setFlash(null), 2500);
      setAssigning(null);
      setAssignTo('');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAssignBusy(false);
    }
  }

  const maxOemTotal = summary.byOem.reduce((m, [, v]) => Math.max(m, v.total), 1);

  return (
    <div className="animate-fade-in-up">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>Vulnerabilities</h1>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{loading ? 'Loading...' : `${filtered.length} of ${items.length} scoped to your organization`}</p>
        </div>
        {isOwner && (
          <button onClick={runScanNow} disabled={scanning} className="btn btn-primary"
            style={{ padding: '0.55rem 1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {scanning ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            {scanning ? 'Queueing...' : 'Run scan now'}
          </button>
        )}
      </div>

      {/* Summary */}
      {!loading && items.length > 0 && (
        <div className="glass-card" style={{ padding: '1rem 1.25rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <BarChart3 size={16} color="#a1a1aa" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#a1a1aa' }}>Overview</span>
            <span style={{ fontSize: '0.75rem', color: '#71717a', marginLeft: 'auto' }}>
              Critical {summary.bySev.critical || 0} · High {summary.bySev.high || 0} · Medium {summary.bySev.medium || 0} · Low {summary.bySev.low || 0}
            </span>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {summary.byOem.slice(0, 10).map(([oem, s]) => (
              <div key={oem} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.8rem' }}>
                <span style={{ width: 110, color: '#a1a1aa', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'pointer' }}
                  onClick={() => setOemFilter(oem === oemFilter ? 'all' : oem)}
                  title="Click to filter">
                  {oem}
                </span>
                <div style={{ flex: 1, display: 'flex', height: 18, borderRadius: 3, overflow: 'hidden', background: 'var(--surface)' }}>
                  {(['critical', 'high', 'medium', 'low'] as const).map(sev => {
                    const count = (s as any)[sev] as number;
                    if (!count) return null;
                    return (
                      <div key={sev} style={{ width: `${(count / maxOemTotal) * 100}%`, background: SEVERITY_COLORS[sev].fg, opacity: 0.7 }} />
                    );
                  })}
                </div>
                <span style={{ width: 40, textAlign: 'right', color: '#d4d4d8', fontFamily: 'var(--font-mono)' }}>{s.total}</span>
              </div>
            ))}
          </div>
          {summary.byOem.length > 10 && (
            <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#71717a', marginTop: '0.5rem' }}>
              +{summary.byOem.length - 10} more OEMs
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5' }}>
          {error}
        </div>
      )}
      {flash && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 8, color: '#86efac', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={16} /> {flash}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 240px', minWidth: 200 }}>
          <SearchIcon size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#71717a' }} />
          <input
            type="text" placeholder="Search CVE, product, description..." value={query} onChange={e => setQuery(e.target.value)}
            style={{ width: '100%', padding: '0.6rem 0.9rem 0.6rem 2.25rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }} />
        </div>
        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}
          style={{ padding: '0.6rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }}>
          <option value="all">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="unknown">Unknown</option>
        </select>
        <select value={oemFilter} onChange={e => setOemFilter(e.target.value)}
          style={{ padding: '0.6rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }}>
          <option value="all">All OEMs</option>
          {oems.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={timeRange} onChange={e => setTimeRange(e.target.value)}
          style={{ padding: '0.6rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }}>
          <option value="all">All time</option>
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      {/* List */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && <>
          <SkeletonRow /><SkeletonRow /><SkeletonRow /><SkeletonRow /><SkeletonRow />
        </>}

        {!loading && filtered.length === 0 && (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <AlertTriangle size={36} color="#71717a" style={{ marginBottom: '0.75rem' }} />
            <h3 style={{ fontSize: '1.05rem', marginBottom: '0.35rem' }}>No vulnerabilities match</h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              {items.length === 0 ? 'Scrapers will populate this view once they run for your enabled OEMs.' : 'Try a different filter.'}
            </p>
          </div>
        )}

        {!loading && filtered.map(v => {
          const sev = sevStyle(v.severity_level);
          const isOpen = expanded.has(v.id);
          const clean = stripHtml(v.vulnerability_description);
          const cleanMitigation = stripHtml(v.mitigation_strategy || '');
          const cves = extractCveIds(v.vulnerability_description || '');
          const isAssigning = assigning === v.id;

          return (
            <div key={v.id} style={{ borderBottom: '1px solid var(--surface-border)' }}>
              <div onClick={() => toggle(v.id)}
                style={{ padding: '0.9rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer', transition: 'background 0.15s' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <span style={{ color: '#71717a', flexShrink: 0 }}>
                  {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </span>
                <span style={{ padding: '0.2rem 0.55rem', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.5px', background: sev.bg, color: sev.fg, textTransform: 'uppercase', flexShrink: 0, minWidth: 70, textAlign: 'center' }}>
                  {v.severity_level || 'Unknown'}
                </span>
                <span style={{ fontWeight: 500, fontFamily: 'var(--font-mono)', fontSize: '0.85rem', flexShrink: 0, minWidth: 140 }}>
                  {v.unique_id}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#71717a', flexShrink: 0, minWidth: 120 }}>
                  {v.oem_name}{v.product_name && v.product_name !== v.oem_name ? ` · ${v.product_name}` : ''}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#a1a1aa', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {clean.slice(0, 200)}
                </span>
                {v.cvss_score && (
                  <span style={{ fontSize: '0.75rem', color: '#71717a', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                    CVSS {v.cvss_score}
                  </span>
                )}
              </div>

              {isOpen && (
                <div style={{ padding: '1rem 1.5rem 1.5rem 3rem', background: 'rgba(0,0,0,0.2)', fontSize: '0.9rem', lineHeight: 1.55 }}>
                  <div style={{ color: '#d4d4d8', marginBottom: '1rem', whiteSpace: 'pre-wrap' }}>{clean}</div>

                  {cves.length > 0 && (
                    <div style={{ marginBottom: '0.9rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.75rem', color: '#71717a', marginRight: '0.25rem' }}>Related CVEs:</span>
                      {cves.map(c => (
                        <span key={c} style={{ padding: '0.15rem 0.45rem', borderRadius: 3, background: 'var(--surface-hover)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>{c}</span>
                      ))}
                    </div>
                  )}

                  {cleanMitigation && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.75rem', color: '#71717a', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mitigation</div>
                      <div style={{ color: '#d4d4d8' }}>{cleanMitigation}</div>
                    </div>
                  )}

                  {v.affected_versions && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.75rem', color: '#71717a', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Affected versions</div>
                      <div style={{ color: '#d4d4d8', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{v.affected_versions}</div>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                    {v.source_url && (
                      <a href={v.source_url} target="_blank" rel="noopener noreferrer"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.4rem 0.75rem', background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: 6, fontSize: '0.8rem', color: '#a1a1aa', textDecoration: 'none' }}>
                        <ExternalLink size={13} /> Source
                      </a>
                    )}

                    {!isAssigning ? (
                      <button onClick={() => { setAssigning(v.id); setAssignTo(''); }}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.4rem 0.75rem', background: 'var(--primary-deep)', border: '1px solid var(--primary)', borderRadius: 6, fontSize: '0.8rem', color: 'var(--primary)', cursor: 'pointer' }}>
                        <UserPlus size={13} /> Assign
                      </button>
                    ) : (
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                        <select value={assignTo} onChange={e => setAssignTo(e.target.value)}
                          style={{ padding: '0.4rem 0.6rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 6, color: 'white', fontSize: '0.8rem' }}>
                          <option value="">Select teammate...</option>
                          {members.map(m => (
                            <option key={m.id} value={m.id}>{m.full_name || m.email} ({m.role})</option>
                          ))}
                        </select>
                        <button onClick={() => submitAssign(v.id)} disabled={!assignTo || assignBusy}
                          style={{ padding: '0.4rem 0.75rem', background: 'var(--primary)', border: 'none', borderRadius: 6, fontSize: '0.8rem', color: '#000', cursor: 'pointer', fontWeight: 600 }}>
                          {assignBusy ? <Loader2 size={13} className="animate-spin" /> : 'Confirm'}
                        </button>
                        <button onClick={() => setAssigning(null)}
                          style={{ padding: '0.4rem 0.75rem', background: 'transparent', border: '1px solid var(--surface-border)', borderRadius: 6, fontSize: '0.8rem', color: '#a1a1aa', cursor: 'pointer' }}>
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
