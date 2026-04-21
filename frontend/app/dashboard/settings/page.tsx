'use client';
import { useEffect, useState } from 'react';
import { Loader2, RefreshCw, Save, Clock, CheckCircle, Mail, Send, MessageSquare } from 'lucide-react';
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
  alert_email: string | null;
  slack_webhook_url: string | null;
  alerts_enabled: boolean;
  alert_min_severity: string;
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
  const [alertEmail, setAlertEmail] = useState<string>('');
  const [slackUrl, setSlackUrl] = useState<string>('');
  const [alertsEnabled, setAlertsEnabled] = useState<boolean>(true);
  const [minSeverity, setMinSeverity] = useState<string>('High');
  const [savingAlerts, setSavingAlerts] = useState(false);
  const [testing, setTesting] = useState(false);
  const [alertFlash, setAlertFlash] = useState<string | null>(null);

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
      setAlertEmail(o.alert_email || '');
      setSlackUrl(o.slack_webhook_url || '');
      setAlertsEnabled(o.alerts_enabled ?? true);
      setMinSeverity(o.alert_min_severity || 'High');
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

  async function saveAlerts() {
    setSavingAlerts(true);
    setError(null);
    try {
      const headers = { ...(await authHeader()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/organizations/settings`, {
        method: 'PATCH', headers,
        body: JSON.stringify({
          alert_email: alertEmail.trim(),
          slack_webhook_url: slackUrl.trim(),
          alerts_enabled: alertsEnabled,
          alert_min_severity: minSeverity,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to save');
      setOrg(await res.json());
      setAlertFlash('Saved');
      setTimeout(() => setAlertFlash(null), 1800);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSavingAlerts(false);
    }
  }

  async function testAlerts() {
    setTesting(true);
    setAlertFlash(null);
    setError(null);
    try {
      const headers = await authHeader();
      const res = await fetch(`${API_URL}/organizations/alerts/test`, { method: 'POST', headers });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.detail || 'Test failed');
      const parts: string[] = [];
      if (payload.email === true) parts.push('email sent');
      else if (payload.email === false) parts.push('email failed (check SMTP env on Render)');
      if (payload.slack === true) parts.push('slack sent');
      else if (payload.slack === false) parts.push('slack failed (check webhook URL)');
      if (parts.length === 0) parts.push('No destination configured — add email or Slack URL first');
      setAlertFlash(parts.join(' · '));
      setTimeout(() => setAlertFlash(null), 5000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setTesting(false);
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
          {/* Alerts card — placed first so Owners see it immediately */}
          <div id="alerts" className="glass-card" style={{ padding: '1.5rem', scrollMarginTop: '80px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Mail size={18} />
                <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Alerts</h2>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#a1a1aa', cursor: isOwner ? 'pointer' : 'default' }}>
                <input type="checkbox" checked={alertsEnabled} disabled={!isOwner}
                  onChange={e => setAlertsEnabled(e.target.checked)} />
                Enabled
              </label>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.85rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: '#a1a1aa', display: 'block', marginBottom: '0.3rem' }}>Alert email</label>
                <input type="email" value={alertEmail} disabled={!isOwner}
                  onChange={e => setAlertEmail(e.target.value)} placeholder="security@yourcompany.com"
                  style={{ width: '100%', padding: '0.55rem 0.8rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', color: '#a1a1aa', display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.3rem' }}>
                  <MessageSquare size={12} /> Slack webhook URL
                </label>
                <input type="url" value={slackUrl} disabled={!isOwner}
                  onChange={e => setSlackUrl(e.target.value)} placeholder="https://hooks.slack.com/services/..."
                  style={{ width: '100%', padding: '0.55rem 0.8rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.78rem', color: '#a1a1aa', display: 'block', marginBottom: '0.3rem' }}>Minimum severity</label>
                <select value={minSeverity} disabled={!isOwner} onChange={e => setMinSeverity(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem 0.8rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'white', fontSize: '0.9rem' }}>
                  {['Critical', 'High', 'Medium', 'Low'].map(s => <option key={s} value={s}>{s}+</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <button onClick={saveAlerts} disabled={!isOwner || savingAlerts} className="btn btn-primary"
                style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                {savingAlerts ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save
              </button>
              <button onClick={testAlerts} disabled={!isOwner || testing}
                style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: 6, color: 'white', fontSize: '0.85rem', cursor: 'pointer' }}>
                {testing ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Send test
              </button>
              {alertFlash && <span style={{ color: '#86efac', fontSize: '0.82rem' }}>{alertFlash}</span>}
            </div>
            <p style={{ fontSize: '0.75rem', color: '#71717a', marginTop: '0.75rem', margin: '0.75rem 0 0 0' }}>
              Digest emails/Slack messages fire automatically after each scheduled scan if new vulnerabilities at this severity or above were found.
            </p>
          </div>

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
