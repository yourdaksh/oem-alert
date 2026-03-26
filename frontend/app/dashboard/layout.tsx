'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Shield, LayoutDashboard, AlertTriangle, CheckSquare, 
  Users, Settings, LogOut, Search, Bell
} from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'Vulnerabilities', path: '/dashboard/vulnerabilities', icon: <AlertTriangle size={20} /> },
    { name: 'My Tasks', path: '/dashboard/tasks', icon: <CheckSquare size={20} /> },
    { name: 'Team', path: '/dashboard/team', icon: <Users size={20} /> },
    { name: 'Settings', path: '/dashboard/settings', icon: <Settings size={20} /> },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--background)' }}>
      {/* Sidebar */}
      <aside className="glass" style={{ width: '260px', borderRight: '1px solid var(--surface-border)', display: 'flex', flexDirection: 'column', position: 'fixed', top: 0, bottom: 0, left: 0, zIndex: 50, borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none' }}>
        <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', borderBottom: '1px solid var(--surface-border)' }}>
          <Shield className="primary-gradient-text" size={28} />
          <h2 style={{ fontSize: '1.25rem', margin: 0 }}>OEM Alert</h2>
        </div>
        
        <div style={{ padding: '1.5rem', flexGrow: 1 }}>
          <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: '#71717a', marginBottom: '1rem', fontWeight: 600 }}>Main Menu</p>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {navItems.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link key={item.name} href={item.path} style={{
                  display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem',
                  borderRadius: '8px', textDecoration: 'none',
                  color: isActive ? 'white' : '#a1a1aa',
                  background: isActive ? 'var(--primary-glow)' : 'transparent',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                  transition: 'all 0.2s',
                  fontWeight: isActive ? 500 : 400
                }}>
                  {item.icon}
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
        
        <div style={{ padding: '1.5rem', borderTop: '1px solid var(--surface-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--surface-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
              👨‍💻
            </div>
            <div>
              <p style={{ fontSize: '0.9rem', fontWeight: 500, margin: 0 }}>Security Admin</p>
              <p style={{ fontSize: '0.75rem', color: '#a1a1aa', margin: 0 }}>Acme Corp</p>
            </div>
          </div>
          <button style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%', padding: '0.75rem', background: 'transparent', border: 'none', color: '#a1a1aa', cursor: 'pointer', textAlign: 'left', borderRadius: '8px' }}>
            <LogOut size={18} />
            <span style={{ fontSize: '0.9rem' }}>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ marginLeft: '260px', flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Navbar */}
        <header className="glass" style={{ height: '70px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2rem', position: 'sticky', top: 0, zIndex: 40, borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none' }}>
          <div style={{ position: 'relative', width: '300px' }}>
            <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#71717a' }} />
            <input 
              type="text" 
              placeholder="Search CVEs, Products..." 
              style={{
                width: '100%', padding: '0.5rem 1rem 0.5rem 2.5rem',
                background: 'rgba(255,255,255,0.03)', border: '1px solid var(--surface-border)',
                borderRadius: '20px', color: 'white', fontSize: '0.9rem', outline: 'none'
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ position: 'relative', cursor: 'pointer' }}>
              <Bell size={20} color="#a1a1aa" />
              <div style={{ position: 'absolute', top: '-2px', right: '-2px', width: '8px', height: '8px', background: 'var(--danger)', borderRadius: '50%' }}></div>
            </div>
          </div>
        </header>
        
        {/* Page Content */}
        <div style={{ padding: '2rem', flexGrow: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
}
