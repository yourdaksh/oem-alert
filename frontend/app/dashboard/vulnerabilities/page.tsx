'use client';
import { useEffect, useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type Vuln = {
  id: string;
  unique_id: string;
  product_name: string;
  oem_name: string;
  severity_level: string;
  published_date: string;
  vulnerability_description: string;
  cvss_score: string | null;
};

const severityColor: Record<string, string> = {
  Critical: 'var(--danger)',
  High: '#fb923c',
  Medium: 'var(--warning)',
  Low: '#a1a1aa',
};

export default function VulnerabilitiesPage() {
  const [items, setItems] = useState<Vuln[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getSupabase().auth.getSession();
        const token = data.session?.access_token;
        if (!token) throw new Error('Not signed in');
        const res = await fetch(`${API_URL}/vulnerabilities/?limit=100`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Failed to load');
        setItems(await res.json());
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
      <div className="flex-between" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Vulnerabilities</h1>
          <p style={{ color: '#a1a1aa' }}>{items.length} scoped to your organization</p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {!error && items.length === 0 && (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <AlertTriangle size={36} color="#71717a" style={{ marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.15rem', marginBottom: '0.5rem' }}>No vulnerabilities yet</h2>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            Scrapers will populate this view once they run for your enabled OEMs.
          </p>
        </div>
      )}

      {items.length > 0 && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          {items.map(v => (
            <div key={v.id} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(255,255,255,0.06)', color: severityColor[v.severity_level] || '#a1a1aa' }}>
                  {v.severity_level?.toUpperCase() || 'UNKNOWN'}
                </span>
                <span style={{ fontWeight: 600 }}>{v.unique_id}</span>
                <span style={{ fontSize: '0.8rem', color: '#71717a' }}>{v.oem_name} · {v.product_name}</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#a1a1aa', lineHeight: 1.5 }}>
                {v.vulnerability_description}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
