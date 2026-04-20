'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ShieldAlert, Mail, Lock, ArrowRight, CheckCircle, User, Loader2 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type InviteInfo = {
  email: string;
  role: string;
  organization_name: string | null;
  expires_at: string;
};

export default function AcceptInvitePage() {
  const params = useParams();
  const router = useRouter();
  const token = Array.isArray(params.token) ? params.token[0] : (params.token as string);

  const [invite, setInvite] = useState<InviteInfo | null>(null);
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/invitation/${token}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Invitation not found');
        setInvite(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/auth/accept-invitation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password, full_name: fullName || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to accept invitation');

      if (invite && data.access_token) {
        await getSupabase().auth.signInWithPassword({ email: invite.email, password });
      }
      setDone(true);
      setTimeout(() => router.push('/dashboard'), 1500);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh' }}>
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  if (!invite) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh', padding: '2rem' }}>
        <div style={{ textAlign: 'center', maxWidth: '420px' }}>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>Invitation unavailable</h1>
          <p style={{ color: '#a1a1aa', marginBottom: '2rem' }}>{error || 'This invitation may have expired or been used.'}</p>
          <Link href="/" className="btn btn-primary" style={{ padding: '0.75rem 1.5rem' }}>Back to home</Link>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh', padding: '2rem' }}>
        <div style={{ textAlign: 'center', maxWidth: '420px' }}>
          <CheckCircle size={48} color="var(--primary)" style={{ marginBottom: '1rem' }} />
          <h1 style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>You&apos;re in!</h1>
          <p style={{ color: '#a1a1aa' }}>Redirecting to your dashboard...</p>
        </div>
      </div>
    );
  }

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '1rem 1rem 1rem 3rem',
    background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)',
    borderRadius: '10px', color: 'white', fontSize: '1rem', outline: 'none',
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <nav style={{ padding: '1.25rem 2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'inherit' }}>
          <ShieldAlert style={{ color: 'var(--primary)' }} size={24} />
          <span style={{ fontSize: '1.15rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>OEM Alert</span>
        </Link>
      </nav>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div className="animate-fade-in-up" style={{ width: '100%', maxWidth: '480px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Join {invite.organization_name || 'the team'}</h1>
            <p style={{ color: '#a1a1aa' }}>
              You&apos;ve been invited as <strong style={{ color: 'var(--primary)' }}>{invite.role}</strong> · <span style={{ color: '#a1a1aa' }}>{invite.email}</span>
            </p>
          </div>

          <div className="glass-card" style={{ padding: '2.5rem' }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <label style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <User size={16} /> Full name (optional)
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                  <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Jane Doe" style={inputStyle} />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Lock size={16} /> Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                  <input type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)} placeholder="Min. 8 characters" style={inputStyle} />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Lock size={16} /> Confirm password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                  <input type="password" required minLength={8} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Re-enter password" style={inputStyle} />
                </div>
              </div>

              {error && (
                <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5', fontSize: '0.9rem' }}>
                  {error}
                </div>
              )}

              <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%', padding: '1rem', fontSize: '1.05rem' }}>
                {submitting ? 'Joining...' : 'Accept Invitation'} <ArrowRight size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
