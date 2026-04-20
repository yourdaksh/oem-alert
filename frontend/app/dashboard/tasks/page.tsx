'use client';
import { useEffect, useState } from 'react';
import { CheckSquare, Loader2 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type Task = {
  id: string;
  vulnerability_id: string;
  status: string;
  assigned_to_id: string | null;
  assigned_by_id: string | null;
  resolution_notes: string | null;
  assigned_at: string;
  updated_at: string;
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        const token = data.session?.access_token;
        if (!token) throw new Error('Not signed in');
        const res = await fetch(`${API_URL}/tasks/`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load');
        setTasks(await res.json());
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div style={{ padding: '2rem' }}><Loader2 className="animate-spin" size={20} /></div>;
  }

  return (
    <div className="animate-fade-in-up">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>My Tasks</h1>
        <p style={{ color: '#a1a1aa' }}>{tasks.length} assigned tasks</p>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {!error && tasks.length === 0 && (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <CheckSquare size={36} color="#71717a" style={{ marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.15rem', marginBottom: '0.5rem' }}>No tasks yet</h2>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            Assign a vulnerability to a teammate from the Vulnerabilities page.
          </p>
        </div>
      )}

      {tasks.length > 0 && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          {tasks.map(t => (
            <div key={t.id} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 500 }}>Vulnerability {t.vulnerability_id.slice(0, 8)}</div>
                <div style={{ fontSize: '0.8rem', color: '#71717a' }}>
                  Assigned {new Date(t.assigned_at).toLocaleDateString()}
                </div>
              </div>
              <span style={{ padding: '0.25rem 0.65rem', borderRadius: '4px', background: 'var(--surface-hover)', fontSize: '0.75rem', color: '#a1a1aa' }}>
                {t.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
