'use client';
import { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Loader2 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type Org = {
  id: string;
  name: string;
  subscription_status: string | null;
  stripe_customer_id: string | null;
  enabled_oems: string | null;
  created_at: string;
};

export default function SettingsPage() {
  const [org, setOrg] = useState<Org | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        const token = data.session?.access_token;
        if (!token) throw new Error('Not signed in');
        const res = await fetch(`${API_URL}/organizations/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load');
        setOrg(await res.json());
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

  const oems = (org?.enabled_oems || '').split(',').map(s => s.trim()).filter(Boolean);

  return (
    <div className="animate-fade-in-up">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Settings</h1>
        <p style={{ color: '#a1a1aa' }}>Organization details.</p>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {org && (
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
      )}
    </div>
  );
}
