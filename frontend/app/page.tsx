'use client';
import Link from 'next/link';
import { Shield, ShieldAlert, Activity, CheckCircle, Clock, Zap, Target, Lock, Users, ArrowRight, Check, Globe, Cpu, Server, Smartphone, Cloud, Database, Radio, Wifi, Monitor, AlertTriangle } from 'lucide-react';

const allOems = [
  'Microsoft','Cisco','VMware','Fortinet','Palo Alto','Apple','Adobe','Intel',
  'Dell','IBM','Oracle','SAP','Juniper','Citrix','HPE','Checkpoint',
  'Red Hat','Ubuntu','Debian','Apache','Nginx','Schneider','Android','Custom'
];

export default function Home() {
  return (
    <div style={{ minHeight: '100vh' }}>
      {/* ─── NAV ─── */}
      <nav className="glass" style={{ padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 100, borderTop: 'none', borderLeft: 'none', borderRight: 'none', borderRadius: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <ShieldAlert style={{ color: 'var(--primary)' }} size={28} />
          <span style={{ fontSize: '1.3rem', fontWeight: 700, letterSpacing: '-1px', fontFamily: 'var(--font-display)' }}>OEM Alert</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Link href="#pricing" style={{ color: 'var(--text-secondary)', textDecoration: 'none', padding: '0.5rem 1rem', fontSize: '0.95rem', fontWeight: 500 }}>Pricing</Link>
          <Link href="/login" className="btn btn-secondary" style={{ padding: '0.6rem 1.25rem' }}>Sign In</Link>
          <Link href="/onboarding" className="btn btn-primary" style={{ padding: '0.6rem 1.25rem' }}>Get Started</Link>
        </div>
      </nav>

      <main>
        {/* ─── HERO ─── */}
        <section style={{ padding: '8rem 2rem 6rem', textAlign: 'center', maxWidth: '950px', margin: '0 auto', position: 'relative' }}>
          <div className="animate-fade-in-up" style={{ display: 'inline-block', padding: '0.3rem 1.25rem', background: 'var(--primary-deep)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: '30px', color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '2.5rem', letterSpacing: '2px', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            ● LIVE — Zero-Day Intelligence Engine
          </div>
          <h1 className="animate-fade-in-up delay-1" style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', lineHeight: 1.08, marginBottom: '1.75rem', fontFamily: 'var(--font-display)' }}>
            Stop Waiting for the NVD.<br/>
            <span className="primary-gradient-text">Secure Your Enterprise</span> with Real-Time OEM Intelligence.
          </h1>
          <p className="animate-fade-in-up delay-2" style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', marginBottom: '3rem', lineHeight: 1.7, maxWidth: '700px', margin: '0 auto 3rem auto' }}>
            The NVD is often weeks behind. Our automated scraping engine monitors <strong style={{ color: '#fff' }}>24+ OEMs</strong> to deliver critical zero-day alerts the second they are published.
          </p>
          <div className="animate-fade-in-up delay-3" style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link href="/onboarding" className="btn btn-primary" style={{ padding: '1.1rem 2.5rem', fontSize: '1.1rem' }}>
              Start 14-Day Free Trial <ArrowRight size={20} />
            </Link>
            <Link href="#pricing" className="btn btn-secondary" style={{ padding: '1.1rem 2.5rem', fontSize: '1.1rem' }}>
              View Pricing
            </Link>
          </div>

          {/* Animated OEM ticker */}
          <div className="animate-fade-in-up delay-4" style={{ marginTop: '4rem', overflow: 'hidden', position: 'relative' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '3px', marginBottom: '1.5rem', fontFamily: 'var(--font-mono)' }}>
              Monitoring 24+ Enterprise OEMs in Real-Time
            </p>
            <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', flexWrap: 'wrap', maxWidth: '800px', margin: '0 auto' }}>
              {allOems.map((oem, i) => (
                <span key={oem} className="animate-fade-in-up" style={{ animationDelay: `${0.6 + i * 0.04}s`, padding: '0.4rem 1rem', background: 'var(--surface)', border: '1px solid var(--surface-border)', borderRadius: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 500, transition: 'all 0.3s ease', cursor: 'default' }}
                  onMouseEnter={(e) => { (e.target as HTMLElement).style.borderColor = 'var(--primary)'; (e.target as HTMLElement).style.color = '#fff'; }}
                  onMouseLeave={(e) => { (e.target as HTMLElement).style.borderColor = 'var(--surface-border)'; (e.target as HTMLElement).style.color = 'var(--text-secondary)'; }}
                >
                  {oem}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* ─── PROBLEM ─── */}
        <section style={{ padding: '6rem 2rem', background: 'linear-gradient(180deg, transparent 0%, rgba(52,211,153,0.02) 100%)', borderTop: '1px solid var(--surface-border)' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)', marginBottom: '1.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600 }}>
              <AlertTriangle size={18} /> THE VULNERABILITY GAP
            </div>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>
              Your Infrastructure is Exposed <span style={{ color: 'var(--danger)' }}>14-21 Days</span> Before the NVD Catches Up.
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.8, marginBottom: '2rem' }}>
              Security engineers manually scrolling through dozens of fragmented OEM portals leads to human error, alert fatigue, and ultimately, critical misses. <strong style={{ color: '#fff' }}>You need a platform that actively hunts for threats, so your team doesn't have to.</strong>
            </p>
            {/* Animated stat counters */}
            <div className="grid grid-3" style={{ marginTop: '3rem', maxWidth: '600px', margin: '3rem auto 0' }}>
              {[
                { num: '24+', label: 'OEMs Monitored' },
                { num: '60s', label: 'Scan Interval' },
                { num: '0 Day', label: 'Alert Latency' }
              ].map((s, i) => (
                <div key={i} className="animate-fade-in-up" style={{ animationDelay: `${i * 0.15}s`, textAlign: 'center' }}>
                  <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--primary)', fontFamily: 'var(--font-display)' }}>{s.num}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '1px' }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ─── LIVE DASHBOARD PREVIEW ─── */}
        <section style={{ padding: '6rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem', textAlign: 'center' }}>See Threats Before They Become Global News.</h2>
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '3rem', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>REAL-TIME DASHBOARD  ·  FILTER: CRITICAL (CVSS 9.0+)</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem', alignItems: 'center' }}>
            {/* Browser mockup with dashboard screenshot */}
            <div className="animate-float" style={{ position: 'relative', width: '100%', maxWidth: '950px', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 25px 80px rgba(52, 211, 153, 0.12), 0 0 0 1px var(--surface-border)' }}>
              <div style={{ background: '#111', padding: '0.85rem 1.25rem', borderBottom: '1px solid #222', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f57' }}></div>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#febc2e' }}></div>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#28c840' }}></div>
                </div>
                <div style={{ flex: 1, textAlign: 'center', fontSize: '0.75rem', color: '#666', fontFamily: 'var(--font-mono)' }}>app.oemalert.io/dashboard</div>
              </div>
              <img src="/assets/dashboard.png" alt="OEM Alert Dashboard" style={{ width: '100%', height: 'auto', display: 'block' }} />
              {/* Scan line effect */}
              <div className="scan-line" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}></div>
            </div>

            {/* Live terminal feed */}
            <div className="glass" style={{ width: '100%', maxWidth: '950px', border: '1px solid rgba(52,211,153,0.2)', boxShadow: '0 0 40px rgba(52,211,153,0.06)', overflow: 'hidden' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem 1.25rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary)', letterSpacing: '2px', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>● Live Terminal Feed</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Auto-refreshing</span>
              </div>
              <div>
                {[
                  { cve: 'CVE-2026-10452', oem: 'VMware vSphere', desc: 'Authentication bypass in vCenter Server allows unauthenticated remote code execution.', severity: 'Critical (9.8)', time: '2 min ago', nvd: 'Unassigned' },
                  { cve: 'CVE-2026-11993', oem: 'Cisco IOS XE', desc: 'Remote Code Execution via crafted HTTP requests to web management interface.', severity: 'Critical (10.0)', time: '14 min ago', nvd: 'Unassigned' },
                  { cve: 'CVE-2026-09221', oem: 'Fortinet FortiOS', desc: 'Heap-based buffer overflow in SSL VPN gateway enables pre-auth exploitation.', severity: 'High (8.8)', time: '1 hr ago', nvd: 'Pending' }
                ].map((vuln, i) => (
                  <div key={i} className="animate-fade-in-up hover-bg" style={{ animationDelay: `${i * 0.2}s`, padding: '1.5rem 1.5rem', borderBottom: i !== 2 ? '1px solid var(--surface-border)' : 'none', display: 'flex', gap: '1.25rem' }}>
                    <div style={{ fontSize: '1.5rem', lineHeight: 1 }}>🚨</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 700, color: 'var(--primary)', fontFamily: 'var(--font-mono)', fontSize: '1rem' }}>{vuln.cve}</span>
                        <span style={{ color: '#444' }}>·</span>
                        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{vuln.oem}</span>
                      </div>
                      <p style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.95rem' }}>{vuln.desc}</p>
                      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', flexWrap: 'wrap' }}>
                        <span style={{ color: vuln.severity.includes('Critical') ? 'var(--danger)' : 'var(--warning)' }}>⬤ {vuln.severity}</span>
                        <span style={{ color: 'var(--text-secondary)' }}>⏱ {vuln.time}</span>
                        <span style={{ color: '#555' }}>NVD: {vuln.nvd}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ─── HOW IT WORKS ─── */}
        <section style={{ padding: '6rem 2rem', background: 'linear-gradient(180deg, transparent 0%, rgba(52,211,153,0.02) 100%)', borderTop: '1px solid var(--surface-border)' }}>
          <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem', textAlign: 'center' }}>From Vendor Publication to SOC Remediation.</h2>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '4rem', fontSize: '1.05rem' }}>Three steps to eliminate the vulnerability gap.</p>
            <div className="grid grid-3">
              {[
                { step: '01', title: 'Map Your Attack Surface', desc: 'Upload your asset inventory or integrate with your CMDB. Select exactly which OEM products and versions you run.', icon: <Target size={28} color="var(--primary)" /> },
                { step: '02', title: 'Continuous Real-Time Scraping', desc: 'Our distributed scraping engine checks 24+ OEM security portals every 60 seconds, fetching zero-day data within minutes.', icon: <Activity size={28} color="var(--primary)" /> },
                { step: '03', title: 'Contextual Alerting & Triage', desc: 'When a new zero-day or CVE drops that matches your stack, we push high-priority alerts with remediation steps.', icon: <Lock size={28} color="var(--primary)" /> }
              ].map((s, i) => (
                <div key={i} className="glass-card" style={{ padding: '2.5rem', textAlign: 'center' }}>
                  <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--primary-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                    {s.icon}
                  </div>
                  <div style={{ color: 'var(--primary)', fontWeight: 700, marginBottom: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', letterSpacing: '2px' }}>{s.step}</div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>{s.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem' }}>{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ─── FEATURES ─── */}
        <section style={{ padding: '6rem 2rem', maxWidth: '1000px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Built for SOC Teams. Designed for Speed.</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>Centralize, normalize, and deliver actionable intelligence instantly.</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {[
              { title: 'Proprietary Instant Scrapers', desc: 'Cloud-based Python web scrapers bypassing static RSS limitations, deeply crawling vendor advisories and fetching zero-day data within minutes of publication.' },
              { title: 'Smart Asset Filtering', desc: "Configure your org's specific asset inventory and CVSS severity thresholds. Only receive highly actionable, context-rich intelligence for products you actually own." },
              { title: 'Automated SOAR & SIEM Integrations', desc: 'Trigger existing security playbooks via native Webhooks, REST APIs, and direct alerts to Slack, Microsoft Teams, and Jira.' },
              { title: 'Unified Compliance Workflows', desc: 'Manage the entire remediation lifecycle. Assign CVEs to team members, track MTTR, and generate executive reports for SOC 2, ISO 27001, and internal compliance audits.' },
            ].map((f, i) => (
              <div key={i} className="hover-bg" style={{ display: 'flex', gap: '1.5rem', padding: '1.75rem', background: 'var(--surface)', borderRadius: '14px', border: '1px solid var(--surface-border)', transition: 'border-color 0.3s ease' }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(52,211,153,0.3)')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--surface-border)')}
              >
                <div style={{ marginTop: '2px', flexShrink: 0 }}><CheckCircle size={22} color="var(--primary)" /></div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', marginBottom: '0.5rem' }}>{f.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem' }}>{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ─── TESTIMONIALS ─── */}
        <section style={{ padding: '6rem 2rem', borderTop: '1px solid var(--surface-border)', background: 'linear-gradient(180deg, transparent, rgba(52,211,153,0.02))' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '4rem' }}>Don't Just Take Our Word For It.</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
              <blockquote style={{ fontSize: '1.2rem', fontStyle: 'italic', fontWeight: 300, lineHeight: 1.8, color: '#ccc' }}>
                "Before OEM Alert, our engineers spent 15 hours a week manually checking Cisco and VMware portals. Now, we get notified of critical flaws days before they hit the NVD."
                <footer style={{ marginTop: '1.25rem', fontStyle: 'normal', fontWeight: 600, color: 'var(--primary)', fontSize: '0.95rem', fontFamily: 'var(--font-mono)' }}>— Sarah J., CISO at GlobalFinance</footer>
              </blockquote>
              <div style={{ width: '60px', height: '1px', background: 'var(--surface-border)', margin: '0 auto' }}></div>
              <blockquote style={{ fontSize: '1.2rem', fontStyle: 'italic', fontWeight: 300, lineHeight: 1.8, color: '#ccc' }}>
                "The NVD lag was killing our SLA for patch management. This platform gave us back the tactical advantage. The targeted asset filtering means we only see what actually matters."
                <footer style={{ marginTop: '1.25rem', fontStyle: 'normal', fontWeight: 600, color: 'var(--primary)', fontSize: '0.95rem', fontFamily: 'var(--font-mono)' }}>— David R., Lead Security Engineer at EnergyGrid</footer>
              </blockquote>
            </div>
          </div>
        </section>

        {/* ─── PRICING (Single $499) ─── */}
        <section style={{ padding: '6rem 2rem', maxWidth: '700px', margin: '0 auto' }} id="pricing">
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Simple, Transparent Pricing.</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>One plan. Full access. No hidden fees.</p>
          </div>

          <div className="glass-card animate-pulse-glow" style={{ padding: '3.5rem', position: 'relative', border: '1px solid rgba(52,211,153,0.3)', textAlign: 'center' }}>
            <div style={{ position: 'absolute', top: '-14px', left: '50%', transform: 'translateX(-50%)', background: 'var(--primary)', color: '#000', padding: '5px 18px', borderRadius: '30px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: '1px' }}>Full Access</div>

            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Enterprise Pro Plan</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Everything you need to eliminate the vulnerability gap.</p>

            <div style={{ fontSize: '4rem', fontWeight: 700, marginBottom: '0.25rem', fontFamily: 'var(--font-display)', lineHeight: 1 }}>
              $499
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '2.5rem', fontFamily: 'var(--font-mono)' }}>per year</div>

            <ul style={{ listStyle: 'none', padding: 0, margin: '0 auto 2.5rem', display: 'flex', flexDirection: 'column', gap: '0.85rem', textAlign: 'left', maxWidth: '400px' }}>
              {[
                'All 24+ OEM Automated Scrapers',
                'Real-Time Email & Slack Alerts',
                'Smart Asset & CVSS Filtering',
                'Unlimited Team Members',
                'REST API Access',
                'Compliance Reports (PDF/CSV)',
                'Kanban Task Management',
                'Priority Support (24hr SLA)'
              ].map((item, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                  <Check size={18} color="var(--primary)" style={{ flexShrink: 0 }} />
                  {item}
                </li>
              ))}
            </ul>

            <Link href="/onboarding" className="btn btn-primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', padding: '1.1rem', fontSize: '1.1rem' }}>
              Start 14-Day Free Trial <ArrowRight size={20} />
            </Link>
            <p style={{ marginTop: '1rem', color: '#555', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>No credit card required to start</p>
          </div>
        </section>

        {/* ─── FAQ ─── */}
        <section style={{ padding: '6rem 2rem', borderTop: '1px solid var(--surface-border)' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '3rem', textAlign: 'center' }}>Frequently Asked Questions</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {[
                { q: 'Why not just use standard CVE threat feeds?', a: 'Standard feeds rely on the NVD, which currently suffers from a massive backlog. By the time a CVE hits standard feeds, hackers are often already exploiting it. We bypass the middleman by scraping vendors directly.' },
                { q: 'Can I add custom or niche OEMs to my monitoring list?', a: 'Yes! We support custom scraper development for any proprietary or niche vendor your organization relies on. Contact us for details.' },
                { q: 'Does this replace my traditional vulnerability scanner?', a: 'No. We are a preemptive threat intelligence platform. Traditional scanners find vulnerabilities already on your network. We alert you the moment a vulnerability is published, often days before scanner plugins are even written.' }
              ].map((faq, i) => (
                <div key={i} className="glass-card" style={{ padding: '1.75rem' }}>
                  <h4 style={{ fontSize: '1.1rem', marginBottom: '0.75rem', color: 'var(--primary)' }}>Q: {faq.q}</h4>
                  <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.95rem' }}>A: {faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* ─── FOOTER ─── */}
      <footer style={{ padding: '4rem 2rem', background: '#000', borderTop: '1px solid var(--surface-border)' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '2rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <ShieldAlert style={{ color: 'var(--primary)' }} size={22} />
              <span style={{ fontSize: '1.15rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>OEM Alert Inc.</span>
            </div>
            <p style={{ color: '#555', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>© 2026 OEM Alert Inc. All rights reserved.</p>
          </div>
          <div style={{ display: 'flex', gap: '2rem', fontSize: '0.85rem' }}>
            <Link href="/privacy" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Privacy</Link>
            <Link href="/terms" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Terms</Link>
            <Link href="/status" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Status</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
