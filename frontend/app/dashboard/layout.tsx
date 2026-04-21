'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Shield, LayoutDashboard, AlertTriangle, CheckSquare,
  Users, Settings, LogOut, Search, Bell, Loader2, Zap, Menu, X,
} from 'lucide-react';
import { getSupabase, API_URL } from '../../lib/supabase';

type OrgInfo = { name: string; subscription_status: string | null };
type Profile = { email: string; role: string; organization: OrgInfo | null };

const MOBILE_BREAKPOINT = 900;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [booted, setBooted] = useState(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`);
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  // Close drawer on route change so tap-through on a link doesn't leave it open
  useEffect(() => { setDrawerOpen(false); }, [pathname]);

  useEffect(() => {
    (async () => {
      const supabase = getSupabase();
      const { data } = await supabase.auth.getSession();
      if (!data.session) { router.replace('/login'); return; }
      try {
        const headers = { Authorization: `Bearer ${data.session.access_token}` };
        const [orgRes, membersRes] = await Promise.all([
          fetch(`${API_URL}/organizations/me`, { headers }),
          fetch(`${API_URL}/organizations/members`, { headers }),
        ]);
        const org = orgRes.ok ? await orgRes.json() : null;
        const members: { id: string; email: string; role: string }[] = membersRes.ok ? await membersRes.json() : [];
        const me = members.find(m => m.id === data.session!.user.id);
        setProfile({
          email: data.session.user.email || me?.email || '',
          role: me?.role || 'Member',
          organization: org ? { name: org.name, subscription_status: org.subscription_status } : null,
        });
      } catch {
        setProfile({ email: data.session.user.email || '', role: 'Member', organization: null });
      }
      setBooted(true);
    })();
  }, [router]);

  async function signOut() {
    await getSupabase().auth.signOut();
    router.replace('/login');
  }

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'Vulnerabilities', path: '/dashboard/vulnerabilities', icon: <AlertTriangle size={20} /> },
    { name: 'Tasks', path: '/dashboard/tasks', icon: <CheckSquare size={20} /> },
    { name: 'Manual Scan', path: '/dashboard/scan', icon: <Zap size={20} /> },
    { name: 'Team', path: '/dashboard/team', icon: <Users size={20} /> },
    { name: 'Settings', path: '/dashboard/settings', icon: <Settings size={20} /> },
  ];

  if (!booted) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh' }}>
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  // Sidebar visibility:
  //   desktop -> always shown, fixed at the left
  //   mobile  -> slides in from the left when drawerOpen=true, hidden otherwise
  const sidebarVisible = !isMobile || drawerOpen;
  const sidebar = (
    <aside className="glass" style={{
      width: 260, position: 'fixed', top: 0, bottom: 0, left: 0, zIndex: 60,
      display: sidebarVisible ? 'flex' : 'none',
      flexDirection: 'column',
      borderRight: '1px solid var(--surface-border)', borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none',
      transform: sidebarVisible ? 'translateX(0)' : 'translateX(-100%)',
      transition: 'transform 0.25s ease',
    }}>
      <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', borderBottom: '1px solid var(--surface-border)', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Shield className="primary-gradient-text" size={28} />
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>OEM Alert</h2>
        </div>
        {isMobile && (
          <button onClick={() => setDrawerOpen(false)} aria-label="Close menu"
            style={{ background: 'transparent', border: 'none', color: '#a1a1aa', cursor: 'pointer', padding: 4 }}>
            <X size={20} />
          </button>
        )}
      </div>

      <div style={{ padding: '1.5rem', flexGrow: 1, overflowY: 'auto' }}>
        <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: '#71717a', marginBottom: '1rem', fontWeight: 600 }}>Main Menu</p>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {navItems.map(item => {
            const isActive = pathname === item.path;
            return (
              <Link key={item.name} href={item.path} style={{
                display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem',
                borderRadius: 8, textDecoration: 'none',
                color: isActive ? 'white' : '#a1a1aa',
                background: isActive ? 'var(--primary-glow)' : 'transparent',
                border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                transition: 'all 0.2s', fontWeight: isActive ? 500 : 400,
              }}>
                {item.icon}
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div style={{ padding: '1.25rem', borderTop: '1px solid var(--surface-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.85rem' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--surface-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 600, flexShrink: 0 }}>
            {profile?.email?.slice(0, 1).toUpperCase() || '?'}
          </div>
          <div style={{ minWidth: 0 }}>
            <p style={{ fontSize: '0.85rem', fontWeight: 500, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{profile?.email || 'Loading...'}</p>
            <p style={{ fontSize: '0.75rem', color: '#a1a1aa', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{profile?.organization?.name || '—'} · {profile?.role}</p>
          </div>
        </div>
        <button onClick={signOut} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%', padding: '0.6rem 0.75rem', background: 'transparent', border: '1px solid var(--surface-border)', color: '#a1a1aa', cursor: 'pointer', textAlign: 'left', borderRadius: 8 }}>
          <LogOut size={16} />
          <span style={{ fontSize: '0.85rem' }}>Sign Out</span>
        </button>
      </div>
    </aside>
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--background)' }}>
      {sidebar}

      {/* Mobile backdrop */}
      {isMobile && drawerOpen && (
        <div onClick={() => setDrawerOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 55 }} />
      )}

      <main style={{ marginLeft: isMobile ? 0 : 260, flexGrow: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header className="glass" style={{
          height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: isMobile ? '0 1rem' : '0 2rem',
          position: 'sticky', top: 0, zIndex: 40,
          borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
            {isMobile && (
              <button onClick={() => setDrawerOpen(true)} aria-label="Open menu"
                style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', padding: 4 }}>
                <Menu size={22} />
              </button>
            )}
            {!isMobile && (
              <div style={{ position: 'relative', width: 300 }}>
                <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#71717a' }} />
                <input type="text" placeholder="Search CVEs, Products..."
                  style={{ width: '100%', padding: '0.5rem 1rem 0.5rem 2.5rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--surface-border)', borderRadius: 20, color: 'white', fontSize: '0.9rem', outline: 'none' }} />
              </div>
            )}
            {isMobile && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
                <Shield className="primary-gradient-text" size={20} />
                <span style={{ fontSize: '0.95rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>OEM Alert</span>
              </div>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ position: 'relative', cursor: 'pointer' }}>
              <Bell size={20} color="#a1a1aa" />
              <div style={{ position: 'absolute', top: -2, right: -2, width: 8, height: 8, background: 'var(--danger)', borderRadius: '50%' }}></div>
            </div>
          </div>
        </header>

        <div style={{ padding: isMobile ? '1.25rem 1rem' : '2rem', flexGrow: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
}
