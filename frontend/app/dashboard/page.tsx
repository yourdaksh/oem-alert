'use client';
import { Activity, AlertTriangle, Eye, ShieldCheck, ChevronRight } from 'lucide-react';

export default function DashboardIndex() {
  const kpis = [
    { title: 'Open Criticals', value: '12', subtitle: '+3 since yesterday', icon: <AlertTriangle size={24} color="var(--danger)" /> },
    { title: 'Total Handled', value: '458', subtitle: 'All time mitigated', icon: <ShieldCheck size={24} color="var(--accent)" /> },
    { title: 'OEMs Monitored', value: '24', subtitle: 'Fully active scrapers', icon: <Activity size={24} color="var(--primary)" /> },
    { title: 'Pending Review', value: '7', subtitle: 'Assigned to your team', icon: <Eye size={24} color="var(--warning)" /> },
  ];

  return (
    <div className="animate-fade-in-up">
      <div className="flex-between" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Command Center</h1>
          <p style={{ color: '#a1a1aa' }}>Overview of your organization's vulnerability landscape.</p>
        </div>
        <button className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>Generate Report</button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-4" style={{ marginBottom: '3rem' }}>
        {kpis.map((kpi, i) => (
          <div key={i} className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="flex-between">
              <span style={{ fontSize: '0.9rem', color: '#a1a1aa', fontWeight: 500 }}>{kpi.title}</span>
              <div style={{ padding: '8px', background: 'var(--surface-hover)', borderRadius: '8px' }}>
                {kpi.icon}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-1px', marginBottom: '0.25rem' }}>{kpi.value}</div>
              <div style={{ fontSize: '0.85rem', color: '#71717a' }}>{kpi.subtitle}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-2">
        {/* Recent Vulnerabilities Feed */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--surface-border)' }} className="flex-between">
            <h2 style={{ fontSize: '1.25rem' }}>Active Vulnerabilities</h2>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.85rem' }}>View All</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {[1, 2, 3, 4].map((_, i) => (
              <div key={i} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'transparent', transition: 'background 0.2s', cursor: 'pointer' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--surface-hover)'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}>CRITICAL</span>
                    <span style={{ fontWeight: 600 }}>CVE-2024-90{i}1</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>VMware vSphere Authentication Bypass</div>
                </div>
                <ChevronRight size={18} color="#71717a" />
              </div>
            ))}
          </div>
        </div>

        {/* My Tasks CRM View */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--surface-border)' }} className="flex-between">
            <h2 style={{ fontSize: '1.25rem' }}>My Tasks</h2>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.85rem' }}>Open Kanban</button>
          </div>
          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
             {[
               { t: 'Review Palo Alto Network Pan-OS patch', status: 'In Progress', color: 'var(--warning)' },
               { t: 'Assess impact of Microsoft Exchange 0-day', status: 'To Do', color: '#a1a1aa' },
               { t: 'Deploy Cisco AnyConnect update to fleet', status: 'Mitigated', color: 'var(--accent)' }
             ].map((task, i) => (
               <div key={i} style={{ padding: '1rem', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ width: '16px', height: '16px', borderRadius: '4px', border: `2px solid ${task.color}` }}></div>
                    <span style={{ fontSize: '0.95rem' }}>{task.t}</span>
                 </div>
                 <span style={{ fontSize: '0.75rem', fontWeight: 500, color: task.color, textTransform: 'uppercase' }}>{task.status}</span>
               </div>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
}
