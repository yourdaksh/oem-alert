'use client';
import { useEffect, useState } from 'react';
import { Loader2, RefreshCw, Save, Clock, CheckCircle } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type Org = {
  id: string;
  name: string;
  subscription_status: string | null;
  stripe_customer_id: string | null;
  enabled_oems: string | null;
  scan_interval_hours: number | null;
  last_scan_at: string | null;
  created_at: string;
};

const INTERVAL_OPTIONS = [
  { hours: 1, label: 'Every hour' },
  { hours: 3, label: 'Every 3 hours' },
  { hours: 6, label: 'Every 6 hours' },
  { hours: 12, label: 'Every 12 hours' },
  { hours: 24, label: 'Daily' },
  { hours: 48, label: 'Every 2 days' },
  { hours: 168, label: 'Weekly' },
];

export default function SettingsPage() {
  const [org, setOrg] = useState<Org | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [interval, setInterval] = useState<number>(6);
  const [savedFlash, setSavedFlash] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string>('');

  async function authHeader(): Promise<Record<string, string>> {
    const { data } = await getSupabase().auth.getSession();
    return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
  }

  async function loadOrg() {
    setError(null);
    try {
      const headers = await authHeader();
      const [orgRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/organizations/me`, { headers }),
        fetch(`${API_URL}/organizations/members`, { headers }),
      ]);
      if (!orgRes.ok) throw new Error((await orgRes.json()).detail || 'Failed to load org');
      const o: Org = await orgRes.json();
      setOrg(o);
      setInterval(o.scan_interval_hours || 6);
      if (membersRes.ok) {
        const { data: user } = await getSupabase().auth.getUser();
        const me = (await membersRes.json()).find((m: any) => m.id === user.user?.id);
        setRole(me?.role || '');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadOrg(); }, []);

  async function saveInterval() {
    setSaving(true);
    setError(null);
    try {
      const headers = { ...(await authHeader()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/organizations/settings`, {
        method: 'PATCH', headers,
        body: JSON.stringify({ scan_interval_hours: interval }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to save');
      setOrg(await res.json());
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 1800);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function runNow() {
    if (!confirm('Start a full scan now? This may take several minutes to complete.')) return;
    setRunning(true);
    setError(null);
    try {
      const headers = { ...(await authHeader()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/scrapers/run`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to queue scan');
      setTimeout(loadOrg, 5000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <div style={{ padding: '2rem' }}><Loader2 className="animate-spin" size={20} /></div>;

  const oems = (org?.enabled_oems || '').split(',').map(s => s.trim()).filter(Boolean);
  const isOwner = role === 'Owner' || role === 'Admin';

  return (
    <div className="animate-fade-in-up">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Settings</h1>
        <p style={{ color: '#a1a1aa' }}>Organization details and scan schedule.</p>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {org && (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {/* Scan schedule card (Owner-only controls) */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Clock size={18} />
              <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Scan schedule</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(160px, 1fr) auto', gap: '0.75rem', alignItems: 'end', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: '#a1a1aa', display: 'block', marginBottom: '0.35rem' }}>
                  Automatic scan frequency
                </label>
                <select value={interval} onChange={e => setInterval(Number(e.target.value))} disabled={!isOwner || saving}
                  style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: '8px', color: 'white', fontSize: '0.95rem' }}>
                  {INTERVAL_OPTIONS.map(o => (
                    <option key={o.hours} value={o.hours}>{o.label}</option>
                  ))}
                </select>
              </div>
              <button onClick={saveInterval} disabled={!isOwner || saving || interval === org.scan_interval_hours} className="btn btn-primary"
                style={{ padding: '0.65rem 1.25rem' }}>
                {saving ? <Loader2 size={16} className="animate-spin" /> : savedFlash ? <CheckCircle size={16} /> : <Save size={16} />}
                {saving ? 'Saving...' : savedFlash ? 'Saved' : 'Save'}
              </button>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: '1rem' }}>
              Last scan: {org.last_scan_at ? new Date(org.last_scan_at).toLocaleString() : 'never'}
            </div>

            {isOwner && (
              <button onClick={runNow} disabled={running} className="btn btn-secondary"
                style={{ padding: '0.55rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {running ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                {running ? 'Queued' : 'Run scan now'}
              </button>
            )}
            {!isOwner && (
              <p style={{ fontSize: '0.8rem', color: '#71717a', margin: 0 }}>
                Only the Owner or an Admin can change the schedule or run a manual scan.
              </p>
            )}
          </div>

          {/* Org info card */}
          <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#71717a', marginBottom: '0.25rem' }}>Organization</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 500 }}>{org.name}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#71717a', marginBottom: '0.25rem' }}>Subscription</div>
              <div style={{ fontSize: '0.95rem' }}>
                {org.subscription_status || 'unknown'}
                {org.stripe_customer_id && <span style={{ color: '#71717a', fontFamily: 'var(--font-mono)', marginLeft: '0.5rem', fontSize: '0.8rem' }}>· {org.stripe_customer_id}</span>}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#71717a', marginBottom: '0.5rem' }}>Monitored OEMs ({oems.length})</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {oems.map(o => (
                  <span key={o} style={{ padding: '0.3rem 0.7rem', background: 'var(--surface-hover)', borderRadius: '4px', fontSize: '0.8rem' }}>{o}</span>
                ))}
                {oems.length === 0 && <span style={{ color: '#71717a', fontSize: '0.85rem' }}>None configured</span>}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#71717a', marginBottom: '0.25rem' }}>Created</div>
              <div style={{ fontSize: '0.9rem', fontFamily: 'var(--font-mono)', color: '#a1a1aa' }}>{new Date(org.created_at).toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
