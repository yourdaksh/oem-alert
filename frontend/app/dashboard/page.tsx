'use client';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, Eye, ShieldCheck, ChevronRight, Download, Loader2, Zap, Sparkles } from 'lucide-react';
import { getSupabase, API_URL } from '../../lib/supabase';
import { stripHtml } from '../../lib/html';

type Vuln = {
  id: string; unique_id: string; oem_name: string; product_name: string;
  severity_level: string; published_date: string; vulnerability_description: string;
  source_url: string | null; cvss_score: string | null;
};
type Task = { id: string; vulnerability_id: string; status: string; assigned_to_id: string | null };

const SEV_COLORS: Record<string, string> = {
  Critical: 'var(--danger)', High: '#fb923c', Medium: 'var(--warning)', Low: 'var(--accent)',
};

function csvEscape(s: string | null | undefined): string {
  const v = (s ?? '').toString();
  if (/[",\n]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
  return v;
}

function exportVulnsCsv(vulns: Vuln[]) {
  const header = ['CVE', 'Severity', 'OEM', 'Product', 'Published', 'CVSS', 'Description', 'Source'];
  const rows = vulns.map(v => [
    v.unique_id, v.severity_level, v.oem_name, v.product_name, v.published_date,
    v.cvss_score || '', stripHtml(v.vulnerability_description).slice(0, 500), v.source_url || '',
  ]);
  const csv = [header, ...rows].map(r => r.map(csvEscape).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `vulnerabilities-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function DashboardIndex() {
  const [vulns, setVulns] = useState<Vuln[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selfId, setSelfId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [hasScanned, setHasScanned] = useState<boolean | null>(null);
  const [orgName, setOrgName] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        const token = data.session?.access_token;
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };
        const [vRes, tRes, uRes, oRes] = await Promise.all([
          fetch(`${API_URL}/vulnerabilities/?limit=2500`, { headers }),
          fetch(`${API_URL}/tasks/`, { headers }),
          getSupabase().auth.getUser(),
          fetch(`${API_URL}/organizations/me`, { headers }),
        ]);
        if (vRes.ok) setVulns(await vRes.json());
        if (tRes.ok) setTasks(await tRes.json());
        setSelfId(uRes.data.user?.id || '');
        if (oRes.ok) {
          const org = await oRes.json();
          setHasScanned(!!org.last_scan_at);
          setOrgName(org.name || '');
        } else {
          setHasScanned(false);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const kpis = useMemo(() => {
    const critical = vulns.filter(v => (v.severity_level || '').toLowerCase() === 'critical').length;
    const handled = tasks.filter(t => /resolved|done|completed/i.test(t.status)).length;
    const oems = new Set(vulns.map(v => v.oem_name)).size;
    const myPending = tasks.filter(t => t.assigned_to_id === selfId && !/resolved|done|completed/i.test(t.status)).length;
    return [
      { title: 'Critical CVEs', value: critical, subtitle: 'In your tracked OEMs', icon: <AlertTriangle size={22} color="var(--danger)" /> },
      { title: 'Resolved', value: handled, subtitle: 'Tasks marked done', icon: <ShieldCheck size={22} color="var(--accent)" /> },
      { title: 'OEMs w/ Data', value: oems, subtitle: `of ${vulns.length} total CVEs`, icon: <Activity size={22} color="var(--primary)" /> },
      { title: 'My Open Tasks', value: myPending, subtitle: 'Assigned to you', icon: <Eye size={22} color="var(--warning)" /> },
    ];
  }, [vulns, tasks, selfId]);

  const recentVulns = useMemo(() => {
    const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    return [...vulns]
      .sort((a, b) => {
        const ra = rank[(a.severity_level || '').toLowerCase()] ?? 4;
        const rb = rank[(b.severity_level || '').toLowerCase()] ?? 4;
        if (ra !== rb) return ra - rb;
        return (b.published_date || '').localeCompare(a.published_date || '');
      })
      .slice(0, 6);
  }, [vulns]);

  const myTasks = useMemo(() => tasks.filter(t => t.assigned_to_id === selfId).slice(0, 5), [tasks, selfId]);

  function handleExport() {
    setExporting(true);
    try { exportVulnsCsv(vulns); } finally { setTimeout(() => setExporting(false), 500); }
  }

  // First-run experience: org has no completed scans yet. Surface a welcome
  // card with a single clear CTA so the owner knows what to do next, instead
  // of staring at a dashboard full of zeros.
  if (!loading && hasScanned === false) {
    return (
      <div className="animate-fade-in-up">
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
            Welcome{orgName ? `, ${orgName}` : ''}
          </h1>
          <p style={{ color: '#a1a1aa' }}>Your organization is ready. Run your first scan to start tracking vulnerabilities.</p>
        </div>

        <div className="glass-card" style={{ padding: '2.5rem', textAlign: 'center', maxWidth: 640, margin: '0 auto' }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--primary-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
            <Sparkles size={28} color="var(--primary)" />
          </div>
          <h2 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>Let&apos;s run your first scan</h2>
          <p style={{ color: '#a1a1aa', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
            We&apos;ll pull the latest advisories from every vendor you subscribed to.
            Takes about <strong>3&ndash;5 minutes</strong>. You can keep using the app
            while it runs &mdash; progress follows you across pages.
          </p>
          <Link href="/dashboard/scan" className="btn btn-primary"
            style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap size={18} /> Run first scan
          </Link>
          <div style={{ marginTop: '1.75rem', fontSize: '0.8rem', color: '#71717a' }}>
            Want automatic scanning? <Link href="/dashboard/settings" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Configure a schedule →</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in-up">
      <div className="flex-between" style={{ marginBottom: '2rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Command Center</h1>
          <p style={{ color: '#a1a1aa' }}>Overview of your organization&apos;s vulnerability landscape.</p>
        </div>
        <button onClick={handleExport} disabled={exporting || vulns.length === 0} className="btn btn-primary"
          style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          Export CSV
        </button>
      </div>

      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        {kpis.map((kpi, i) => (
          <div key={i} className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div className="flex-between">
              <span style={{ fontSize: '0.9rem', color: '#a1a1aa', fontWeight: 500 }}>{kpi.title}</span>
              <div style={{ padding: 8, background: 'var(--surface-hover)', borderRadius: 8 }}>{kpi.icon}</div>
            </div>
            <div>
              <div style={{ fontSize: '2.25rem', fontWeight: 700, letterSpacing: '-1px', marginBottom: '0.15rem' }}>
                {loading ? <Loader2 className="animate-spin" size={24} /> : kpi.value}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#71717a' }}>{kpi.subtitle}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-2">
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Top CVEs</h2>
            <Link href="/dashboard/vulnerabilities" style={{ fontSize: '0.8rem', color: 'var(--primary)', textDecoration: 'none' }}>View all →</Link>
          </div>
          <div>
            {loading && <div style={{ padding: '2rem', textAlign: 'center' }}><Loader2 className="animate-spin" size={18} /></div>}
            {!loading && recentVulns.length === 0 && (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#a1a1aa', fontSize: '0.9rem' }}>No vulnerabilities yet.</div>
            )}
            {!loading && recentVulns.map(v => (
              <Link key={v.id} href="/dashboard/vulnerabilities"
                style={{ padding: '0.85rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', textDecoration: 'none', color: 'inherit' }}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.2rem' }}>
                    <span style={{ padding: '2px 7px', borderRadius: 3, fontSize: '0.7rem', fontWeight: 600,
                      background: `${SEV_COLORS[v.severity_level] || '#71717a'}22`,
                      color: SEV_COLORS[v.severity_level] || '#a1a1aa' }}>
                      {(v.severity_level || 'UNKNOWN').toUpperCase()}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{v.unique_id}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#a1a1aa', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {v.oem_name} · {stripHtml(v.vulnerability_description).slice(0, 80)}
                  </div>
                </div>
                <ChevronRight size={16} color="#71717a" />
              </Link>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.1rem', margin: 0 }}>My Tasks</h2>
            <Link href="/dashboard/tasks" style={{ fontSize: '0.8rem', color: 'var(--primary)', textDecoration: 'none' }}>Open Kanban →</Link>
          </div>
          <div style={{ padding: '1rem' }}>
            {loading && <div style={{ padding: '1rem', textAlign: 'center' }}><Loader2 className="animate-spin" size={18} /></div>}
            {!loading && myTasks.length === 0 && (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#a1a1aa', fontSize: '0.9rem' }}>
                Nothing assigned to you yet.
              </div>
            )}
            {!loading && myTasks.map(t => (
              <div key={t.id} style={{ padding: '0.75rem 1rem', background: 'var(--surface)', borderRadius: 8, border: '1px solid var(--surface-border)', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>Task {t.id.slice(0, 8)}</span>
                <span style={{ fontSize: '0.72rem', color: '#a1a1aa', padding: '0.15rem 0.5rem', background: 'var(--surface-hover)', borderRadius: 3 }}>{t.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
