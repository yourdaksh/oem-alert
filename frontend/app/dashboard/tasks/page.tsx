'use client';
import { useEffect, useMemo, useState } from 'react';
import { CheckSquare, Loader2, User as UserIcon, ExternalLink, ChevronDown } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';
import { stripHtml } from '../../../lib/html';

type Task = {
  id: string;
  vulnerability_id: string;
  organization_id: string;
  status: string;
  assigned_to_id: string | null;
  assigned_by_id: string | null;
  resolution_notes: string | null;
  assigned_at: string;
  updated_at: string;
};

type Vuln = {
  id: string;
  unique_id: string;
  oem_name: string;
  product_name: string;
  severity_level: string;
  vulnerability_description: string;
  source_url: string | null;
};

type Member = { id: string; email: string; full_name: string | null; role: string };

const COLUMNS = [
  { key: 'Assigned', title: 'To Do', accent: '#a1a1aa' },
  { key: 'In Progress', title: 'In Progress', accent: 'var(--warning)' },
  { key: 'Resolved', title: 'Resolved', accent: 'var(--accent)' },
];

const STATUS_MAP: Record<string, string> = {
  'assigned': 'Assigned',
  'in progress': 'In Progress',
  'in_progress': 'In Progress',
  'resolved': 'Resolved',
  'done': 'Resolved',
  'completed': 'Resolved',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#fca5a5', high: '#fdba74', medium: '#fde68a', moderate: '#fde68a',
  low: '#86efac', unknown: '#d4d4d8',
};

function normalizeStatus(s: string): string {
  return STATUS_MAP[(s || '').toLowerCase()] || 'Assigned';
}

function Card({
  task, vuln, members, onMove, busy,
}: {
  task: Task; vuln: Vuln | undefined; members: Member[];
  onMove: (id: string, next: string) => void; busy: boolean;
}) {
  const assignee = members.find(m => m.id === task.assigned_to_id);
  const sev = (vuln?.severity_level || 'unknown').toLowerCase();
  return (
    <div className="glass-card" style={{ padding: '0.85rem', marginBottom: '0.65rem', borderLeft: `3px solid ${SEVERITY_COLORS[sev] || '#71717a'}` }}>
      {vuln ? (
        <>
          <div style={{ fontSize: '0.72rem', color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.25rem' }}>
            {vuln.oem_name} · {vuln.severity_level}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', marginBottom: '0.35rem', fontWeight: 500 }}>
            {vuln.unique_id}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#d4d4d8', marginBottom: '0.5rem', maxHeight: 48, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', lineHeight: 1.4 }}>
            {stripHtml(vuln.vulnerability_description).slice(0, 160)}
          </div>
        </>
      ) : (
        <div style={{ fontSize: '0.8rem', color: '#a1a1aa', marginBottom: '0.5rem' }}>
          Vulnerability {task.vulnerability_id.slice(0, 8)}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.72rem', color: '#71717a' }}>
          <UserIcon size={11} />
          <span style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {assignee ? (assignee.full_name || assignee.email) : 'Unassigned'}
          </span>
        </div>

        <div style={{ position: 'relative' }}>
          <select value={normalizeStatus(task.status)} onChange={e => onMove(task.id, e.target.value)} disabled={busy}
            style={{ appearance: 'none', padding: '0.25rem 1.5rem 0.25rem 0.5rem', background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: 4, color: '#d4d4d8', fontSize: '0.72rem', cursor: 'pointer' }}>
            {COLUMNS.map(c => <option key={c.key} value={c.key}>{c.title}</option>)}
          </select>
          <ChevronDown size={10} style={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#71717a' }} />
        </div>
      </div>

      {vuln?.source_url && (
        <a href={vuln.source_url} target="_blank" rel="noopener noreferrer"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.5rem', fontSize: '0.7rem', color: '#71717a', textDecoration: 'none' }}>
          <ExternalLink size={10} /> Source
        </a>
      )}
    </div>
  );
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [vulns, setVulns] = useState<Record<string, Vuln>>({});
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'mine'>('all');
  const [selfId, setSelfId] = useState<string>('');

  async function authHeaders(): Promise<Record<string, string>> {
    const { data } = await getSupabase().auth.getSession();
    return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
  }

  async function loadAll() {
    setError(null);
    try {
      const headers = await authHeaders();
      const [tRes, mRes, uRes] = await Promise.all([
        fetch(`${API_URL}/tasks/`, { headers }),
        fetch(`${API_URL}/organizations/members`, { headers }),
        getSupabase().auth.getUser(),
      ]);
      if (!tRes.ok) throw new Error((await tRes.json()).detail || 'Failed to load tasks');
      const t: Task[] = await tRes.json();
      setTasks(t);
      if (mRes.ok) setMembers(await mRes.json());
      setSelfId(uRes.data.user?.id || '');

      // Hydrate vuln details for the task set in parallel
      const vulnIds = Array.from(new Set(t.map(x => x.vulnerability_id)));
      const results = await Promise.all(vulnIds.map(id =>
        fetch(`${API_URL}/vulnerabilities/${id}`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null)
      ));
      const map: Record<string, Vuln> = {};
      results.forEach(v => { if (v) map[v.id] = v; });
      setVulns(map);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, []);

  async function moveTask(id: string, nextStatus: string) {
    setUpdating(p => { const n = new Set(p); n.add(id); return n; });
    try {
      const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/tasks/${id}`, {
        method: 'PATCH', headers,
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to update');
      setTasks(prev => prev.map(t => t.id === id ? { ...t, status: nextStatus } : t));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUpdating(p => { const n = new Set(p); n.delete(id); return n; });
    }
  }

  const scoped = useMemo(() => filter === 'mine'
    ? tasks.filter(t => t.assigned_to_id === selfId)
    : tasks, [tasks, filter, selfId]);

  const byColumn = useMemo(() => {
    const out: Record<string, Task[]> = { Assigned: [], 'In Progress': [], Resolved: [] };
    for (const t of scoped) {
      out[normalizeStatus(t.status)]?.push(t);
    }
    return out;
  }, [scoped]);

  return (
    <div className="animate-fade-in-up">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>Tasks</h1>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            {loading ? 'Loading...' : `${scoped.length} ${filter === 'mine' ? 'assigned to you' : 'in your organization'}`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', background: 'var(--surface)', border: '1px solid var(--surface-border)', padding: '0.25rem', borderRadius: 8 }}>
          {(['all', 'mine'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{ padding: '0.4rem 0.9rem', background: filter === f ? 'var(--surface-hover)' : 'transparent', border: 'none', borderRadius: 6, fontSize: '0.85rem', color: filter === f ? 'white' : '#a1a1aa', cursor: 'pointer', fontWeight: filter === f ? 500 : 400 }}>
              {f === 'all' ? 'All tasks' : 'Assigned to me'}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '2rem', textAlign: 'center' }}><Loader2 className="animate-spin" size={20} /></div>
      ) : tasks.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <CheckSquare size={36} color="#71717a" style={{ marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>No tasks yet</h3>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            Open a vulnerability and click <strong>Assign</strong> to create a task for a teammate.
          </p>
        </div>
      ) : (
        <div className="kanban-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '1rem' }}>
          {COLUMNS.map(col => (
            <div key={col.key} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--surface-border)', borderRadius: 10, padding: '0.85rem', minHeight: 300 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: col.accent }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{col.title}</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#71717a', padding: '0.1rem 0.45rem', background: 'var(--surface-hover)', borderRadius: 8 }}>
                  {byColumn[col.key]?.length || 0}
                </span>
              </div>
              <div>
                {(byColumn[col.key] || []).map(task => (
                  <Card key={task.id} task={task} vuln={vulns[task.vulnerability_id]} members={members}
                    onMove={moveTask} busy={updating.has(task.id)} />
                ))}
                {(byColumn[col.key] || []).length === 0 && (
                  <div style={{ padding: '1.5rem 0.5rem', textAlign: 'center', fontSize: '0.8rem', color: '#71717a' }}>
                    No tasks here
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
