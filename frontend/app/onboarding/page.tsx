'use client';
import { useState } from 'react';
import { Shield, ShieldAlert, Check, ArrowRight, Mail, Building, Lock, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    organizationName: '',
    email: '',
    password: '',
    selectedOems: [] as string[]
  });

  const allOems = [
    'Microsoft','Cisco','VMware','Fortinet','Palo Alto','Apple','Adobe','Intel',
    'Dell','IBM','Oracle','SAP','Juniper','Citrix','HPE','Checkpoint',
    'Red Hat','Ubuntu','Debian','Apache','Nginx','Schneider','Android','Custom'
  ];

  const handleOemToggle = (oem: string) => {
    if (formData.selectedOems.includes(oem)) {
      setFormData({ ...formData, selectedOems: formData.selectedOems.filter(o => o !== oem) });
    } else {
      setFormData({ ...formData, selectedOems: [...formData.selectedOems, oem] });
    }
  };

  const selectAllOems = () => {
    if (formData.selectedOems.length === allOems.length) {
      setFormData({ ...formData, selectedOems: [] });
    } else {
      setFormData({ ...formData, selectedOems: [...allOems] });
    }
  };

  const handleCheckout = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/payments/onboarding-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to create checkout session');
      window.location.href = data.checkout_url;
    } catch (error: any) {
      alert("Checkout Error: " + error.message);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Nav */}
      <nav style={{ padding: '1.25rem 2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', color: 'inherit' }}>
          <ShieldAlert style={{ color: 'var(--primary)' }} size={24} />
          <span style={{ fontSize: '1.15rem', fontWeight: 700, fontFamily: 'var(--font-display)', letterSpacing: '-0.5px' }}>OEM Alert</span>
        </Link>
      </nav>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div className="animate-fade-in-up" style={{ width: '100%', maxWidth: step === 2 ? '750px' : '520px', transition: 'max-width 0.4s ease' }}>

          {/* Progress */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginBottom: '2.5rem' }}>
            {[1, 2].map(s => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  background: step >= s ? 'var(--primary)' : 'var(--surface)',
                  border: step >= s ? 'none' : '1px solid var(--surface-border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: step >= s ? '#000' : 'var(--text-secondary)',
                  fontWeight: 700, fontSize: '0.85rem', fontFamily: 'var(--font-mono)',
                  transition: 'all 0.3s ease'
                }}>
                  {step > s ? <Check size={16} /> : s}
                </div>
                <span style={{ fontSize: '0.85rem', color: step >= s ? '#fff' : 'var(--text-secondary)', fontWeight: step === s ? 600 : 400 }}>
                  {s === 1 ? 'Organization' : 'Select OEMs & Pay'}
                </span>
                {s === 1 && <div style={{ width: '40px', height: '1px', background: step > 1 ? 'var(--primary)' : 'var(--surface-border)', margin: '0 0.5rem', transition: 'background 0.3s ease' }}></div>}
              </div>
            ))}
          </div>

          <div className="glass-card" style={{ padding: '3rem' }}>
            {/* Step 1: Organization Info */}
            {step === 1 && (
              <div className="animate-fade-in">
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                  <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'var(--primary-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem' }}>
                    <Shield style={{ color: 'var(--primary)' }} size={28} />
                  </div>
                  <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', fontFamily: 'var(--font-display)' }}>Welcome to OEM Alert</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Tell us about your organization to get started.</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Building size={16} /> Organization Name
                    </label>
                    <input
                      type="text" className="input-field"
                      placeholder="e.g. Acme Security Corp"
                      value={formData.organizationName}
                      onChange={e => setFormData({...formData, organizationName: e.target.value})}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      <Mail size={16} /> Security Admin Email
                    </label>
                    <input
                      type="email" className="input-field"
                      placeholder="admin@yourcompany.com"
                      value={formData.email}
                      onChange={e => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '1rem', fontSize: '1.05rem', marginTop: '0.5rem' }}
                    onClick={() => setStep(2)}
                    disabled={!formData.organizationName || !formData.email}
                  >
                    Continue <ArrowRight size={18} />
                  </button>
                </div>

                <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#555', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                  Already have an account? <Link href="/login" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Sign in</Link>
                </p>
              </div>
            )}

            {/* Step 2: OEM Selection + Checkout */}
            {step === 2 && (
              <div className="animate-fade-in">
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                  <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', fontFamily: 'var(--font-display)' }}>Select OEMs to Monitor</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Choose which vendors to track. You can change this anytime later.</p>
                </div>

                {/* Select All */}
                <button
                  onClick={selectAllOems}
                  style={{
                    width: '100%', padding: '0.75rem', marginBottom: '1rem',
                    background: formData.selectedOems.length === allOems.length ? 'var(--primary-deep)' : 'var(--surface)',
                    border: `1px solid ${formData.selectedOems.length === allOems.length ? 'var(--primary)' : 'var(--surface-border)'}`,
                    borderRadius: '10px', color: formData.selectedOems.length === allOems.length ? 'var(--primary)' : 'var(--text-secondary)',
                    cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, transition: 'all 0.2s ease'
                  }}
                >
                  {formData.selectedOems.length === allOems.length ? '✓ All Selected' : 'Select All 24 OEMs'}
                </button>

                {/* OEM Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.6rem', marginBottom: '2rem', maxHeight: '320px', overflowY: 'auto', padding: '0.5rem 0' }}>
                  {allOems.map(oem => {
                    const isSelected = formData.selectedOems.includes(oem);
                    return (
                      <div
                        key={oem}
                        onClick={() => handleOemToggle(oem)}
                        style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                          padding: '0.75rem 0.5rem', borderRadius: '10px', cursor: 'pointer',
                          border: isSelected ? '1px solid var(--primary)' : '1px solid var(--surface-border)',
                          background: isSelected ? 'var(--primary-deep)' : 'var(--surface)',
                          transition: 'all 0.2s ease', fontSize: '0.85rem',
                          color: isSelected ? '#fff' : 'var(--text-secondary)', fontWeight: isSelected ? 600 : 400
                        }}
                      >
                        {isSelected && <Check size={14} color="var(--primary)" />}
                        {oem}
                      </div>
                    );
                  })}
                </div>

                {/* Summary */}
                <div style={{ background: 'var(--surface)', border: '1px solid var(--surface-border)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Enterprise Pro Plan</span>
                    <span style={{ fontWeight: 700, fontFamily: 'var(--font-display)', fontSize: '1.5rem' }}>$499<span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 400 }}>/year</span></span>
                  </div>
                  <div style={{ color: '#555', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                    {formData.selectedOems.length} OEM{formData.selectedOems.length !== 1 ? 's' : ''} selected · {formData.organizationName}
                  </div>
                </div>

                {/* Action buttons */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem' }}>
                  <button className="btn btn-secondary" style={{ padding: '1rem' }} onClick={() => setStep(1)}>Back</button>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '1rem', fontSize: '1.05rem' }}
                    onClick={handleCheckout}
                    disabled={formData.selectedOems.length === 0 || isLoading}
                  >
                    {isLoading ? (
                      <><span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', width: '18px', height: '18px', border: '2px solid transparent', borderTopColor: '#000', borderRadius: '50%' }}></span> Processing...</>
                    ) : (
                      <>Proceed to Stripe Checkout <ArrowRight size={18} /></>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
