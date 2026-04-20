'use client';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { useState, Suspense } from 'react';
import { ShieldAlert, Mail, Lock, ArrowRight, CheckCircle, Eye, EyeOff, Building } from 'lucide-react';
import { getSupabase, API_URL } from '../../lib/supabase';

function LoginContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const isOnboarded = searchParams.get('onboarded') === 'true';
  const sessionId = searchParams.get('session_id') || '';

  const [mode, setMode] = useState<'login' | 'setup'>(isOnboarded ? 'setup' : 'login');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [setupDone, setSetupDone] = useState(false);

  const [email, setEmail] = useState('');
  const [orgName, setOrgName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId) {
      alert('Missing checkout session — please complete payment first.');
      return;
    }
    if (password.length < 8) { alert('Password must be at least 8 characters.'); return; }
    if (password !== confirmPassword) { alert('Passwords do not match.'); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/setup-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          organizationName: orgName,
          stripeSessionId: sessionId,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Setup failed');

      setSetupDone(true);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const supabase = getSupabase();
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      router.push('/dashboard');
    } catch (err: any) {
      alert(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '1rem 1rem 1rem 3rem',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid var(--surface-border)',
    borderRadius: '10px',
    color: 'white',
    fontSize: '1rem',
    fontFamily: 'var(--font-sans)',
    outline: 'none',
    transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
  } as const;

  if (setupDone) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh', padding: '2rem' }}>
        <div className="animate-fade-in-up" style={{ width: '100%', maxWidth: '480px', textAlign: 'center' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--primary-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem' }}>
            <CheckCircle size={40} color="var(--primary)" />
          </div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.75rem', fontFamily: 'var(--font-display)' }}>Account Created!</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', marginBottom: '2.5rem', lineHeight: 1.7 }}>
            Your organization is provisioned. Sign in to access your dashboard.
          </p>
          <button className="btn btn-primary" style={{ padding: '1rem 2.5rem', fontSize: '1.05rem' }}
            onClick={() => { setMode('login'); setSetupDone(false); }}>
            Sign In to Dashboard <ArrowRight size={18} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <nav style={{ padding: '1.25rem 2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'inherit' }}>
          <ShieldAlert style={{ color: 'var(--primary)' }} size={24} />
          <span style={{ fontSize: '1.15rem', fontWeight: 700, fontFamily: 'var(--font-display)', letterSpacing: '-0.5px' }}>OEM Alert</span>
        </Link>
      </nav>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div className="animate-fade-in-up" style={{ width: '100%', maxWidth: '480px' }}>

          {mode === 'setup' && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                <div style={{ display: 'inline-flex', padding: '0.3rem 1rem', background: 'var(--primary-deep)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: '30px', color: 'var(--primary)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '1.5rem', fontFamily: 'var(--font-mono)', letterSpacing: '1px', textTransform: 'uppercase' }}>
                  ✓ Payment Successful
                </div>
                <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontFamily: 'var(--font-display)' }}>Set Up Your Account</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Create a password to access your vulnerability dashboard.</p>
              </div>

              <div className="glass-card" style={{ padding: '2.5rem' }}>
                <form onSubmit={handleSetup} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Building size={16} /> Organization Name
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Building size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type="text" placeholder="Your organization name" value={orgName} onChange={e => setOrgName(e.target.value)} style={inputStyle} required />
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Mail size={16} /> Email Address
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Mail size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type="email" placeholder="Your email from checkout" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} required />
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Lock size={16} /> Create Password
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type={showPassword ? 'text' : 'password'} placeholder="Min. 8 characters" value={password} onChange={e => setPassword(e.target.value)} style={inputStyle} required minLength={8} />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#555', cursor: 'pointer', padding: 0 }}>
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Lock size={16} /> Confirm Password
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type={showConfirm ? 'text' : 'password'} placeholder="Re-enter password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={inputStyle} required minLength={8} />
                      <button type="button" onClick={() => setShowConfirm(!showConfirm)} style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#555', cursor: 'pointer', padding: 0 }}>
                        {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', padding: '1rem', fontSize: '1.05rem', marginTop: '0.5rem', opacity: loading ? 0.7 : 1 }}>
                    {loading ? 'Setting up...' : 'Create Account'} <ArrowRight size={18} />
                  </button>
                </form>
              </div>

              <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#444', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                Already have an account? <span onClick={() => setMode('login')} style={{ color: 'var(--primary)', cursor: 'pointer' }}>Sign in instead</span>
              </p>
            </>
          )}

          {mode === 'login' && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'var(--primary-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
                  <ShieldAlert style={{ color: 'var(--primary)' }} size={28} />
                </div>
                <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontFamily: 'var(--font-display)' }}>Welcome Back</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Enter your credentials to access your dashboard.</p>
              </div>

              <div className="glass-card" style={{ padding: '2.5rem' }}>
                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Mail size={16} /> Email Address
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Mail size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type="email" placeholder="name@company.com" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} required />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                        <Lock size={16} /> Password
                      </label>
                    </div>
                    <div style={{ position: 'relative' }}>
                      <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#555' }} />
                      <input type={showPassword ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} style={inputStyle} required />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#555', cursor: 'pointer', padding: 0 }}>
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', padding: '1rem', fontSize: '1.05rem', marginTop: '0.5rem', opacity: loading ? 0.7 : 1 }}>
                    {loading ? 'Signing in...' : 'Sign In'} <ArrowRight size={18} />
                  </button>
                </form>
              </div>

              <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#444', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                Don&apos;t have an account? <Link href="/onboarding" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Get Started</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex-center" style={{ minHeight: '100vh' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Loading...</p>
      </div>
    }>
      <LoginContent />
    </Suspense>
  );
}
