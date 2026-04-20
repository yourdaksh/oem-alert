'use client';
import { useEffect, useState } from 'react';
import { Users, Mail, Trash2, Copy, UserPlus, Shield, Loader2 } from 'lucide-react';
import { getSupabase, API_URL } from '../../../lib/supabase';

type Member = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
};

type Invitation = {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
  invited_by: string | null;
  token: string | null;
};

const ROLES = ['Admin', 'Analyst', 'Viewer'];

export default function TeamPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Analyst');
  const [inviting, setInviting] = useState(false);
  const [copiedInviteId, setCopiedInviteId] = useState<string | null>(null);
  const [selfRole, setSelfRole] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  async function authHeaders(): Promise<Record<string, string>> {
    const { data } = await getSupabase().auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async function refresh() {
    setError(null);
    try {
      const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
      const [membersRes, invitesRes] = await Promise.all([
        fetch(`${API_URL}/organizations/members`, { headers }),
        fetch(`${API_URL}/organizations/invitations`, { headers }),
      ]);
      if (!membersRes.ok) throw new Error((await membersRes.json()).detail || 'Failed to load members');
      const membersData: Member[] = await membersRes.json();
      setMembers(membersData);

      const { data: user } = await getSupabase().auth.getUser();
      const me = membersData.find(m => m.id === user.user?.id);
      setSelfRole(me?.role || '');

      if (invitesRes.ok) {
        setInvites(await invitesRes.json());
      } else {
        setInvites([]);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    setInviting(true);
    setError(null);
    try {
      const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/organizations/invite`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create invitation');
      setInviteEmail('');
      await navigator.clipboard.writeText(data.invite_url).catch(() => {});
      await refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setInviting(false);
    }
  }

  async function revokeInvite(id: string) {
    const headers = { ...(await authHeaders()) };
    const res = await fetch(`${API_URL}/organizations/invitations/${id}`, { method: 'DELETE', headers });
    if (!res.ok) setError((await res.json()).detail || 'Failed to revoke');
    await refresh();
  }

  async function copyInviteLink(token: string, id: string) {
    const url = `${window.location.origin}/invite/${token}`;
    await navigator.clipboard.writeText(url);
    setCopiedInviteId(id);
    setTimeout(() => setCopiedInviteId(null), 1500);
  }

  async function changeRole(userId: string, role: string) {
    const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
    const res = await fetch(`${API_URL}/organizations/members/${userId}/role`, {
      method: 'PATCH', headers, body: JSON.stringify({ role }),
    });
    if (!res.ok) setError((await res.json()).detail || 'Failed to update role');
    await refresh();
  }

  async function removeMember(userId: string) {
    if (!confirm('Remove this member from the organization?')) return;
    const headers = { ...(await authHeaders()) };
    const res = await fetch(`${API_URL}/organizations/members/${userId}`, { method: 'DELETE', headers });
    if (!res.ok) setError((await res.json()).detail || 'Failed to remove');
    await refresh();
  }

  const isOwner = selfRole === 'Owner' || selfRole === 'Admin';

  if (loading) {
    return <div style={{ padding: '2rem', color: '#a1a1aa' }}><Loader2 className="animate-spin" size={20} /> Loading...</div>;
  }

  return (
    <div className="animate-fade-in-up">
      <div className="flex-between" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Team</h1>
          <p style={{ color: '#a1a1aa' }}>Manage members and invitations for your organization.</p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1.5rem', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      {isOwner && (
        <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <UserPlus size={18} /> Invite teammate
          </h2>
          <form onSubmit={handleInvite} style={{ display: 'flex', gap: '0.75rem', alignItems: 'end', flexWrap: 'wrap' }}>
            <div style={{ flex: '2 1 240px' }}>
              <label style={{ fontSize: '0.8rem', color: '#a1a1aa', display: 'block', marginBottom: '0.35rem' }}>Email</label>
              <input type="email" required value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="name@company.com"
                style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: '8px', color: 'white', fontSize: '0.95rem' }} />
            </div>
            <div style={{ flex: '1 1 140px' }}>
              <label style={{ fontSize: '0.8rem', color: '#a1a1aa', display: 'block', marginBottom: '0.35rem' }}>Role</label>
              <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}
                style={{ width: '100%', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: '8px', color: 'white', fontSize: '0.95rem' }}>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={inviting}
              style={{ padding: '0.65rem 1.25rem' }}>
              {inviting ? <Loader2 size={16} className="animate-spin" /> : <Mail size={16} />}
              {inviting ? 'Sending...' : 'Send invite'}
            </button>
          </form>
          <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#71717a' }}>
            Invite link copied to clipboard on send. Expires in 7 days.
          </p>
        </div>
      )}

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden', marginBottom: '2rem' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={18} /> <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Members ({members.length})</h2>
        </div>
        <div>
          {members.map(m => (
            <div key={m.id} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 500 }}>{m.full_name || m.email}</div>
                <div style={{ fontSize: '0.8rem', color: '#71717a' }}>{m.email}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                {isOwner && m.role !== 'Owner' ? (
                  <select value={m.role} onChange={e => changeRole(m.id, e.target.value)}
                    style={{ padding: '0.35rem 0.6rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--surface-border)', borderRadius: '6px', color: 'white', fontSize: '0.85rem' }}>
                    {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                ) : (
                  <span style={{ padding: '0.25rem 0.6rem', borderRadius: '4px', background: 'var(--surface-hover)', fontSize: '0.75rem', color: '#a1a1aa', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <Shield size={12} /> {m.role}
                  </span>
                )}
                {isOwner && m.role !== 'Owner' && (
                  <button onClick={() => removeMember(m.id)}
                    style={{ background: 'transparent', border: '1px solid var(--surface-border)', borderRadius: '6px', padding: '0.35rem', cursor: 'pointer', color: '#f87171' }}
                    title="Remove">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {isOwner && invites.length > 0 && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--surface-border)' }}>
            <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Invitations</h2>
          </div>
          <div>
            {invites.map(inv => (
              <div key={inv.id} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 500 }}>{inv.email}</div>
                  <div style={{ fontSize: '0.8rem', color: '#71717a' }}>
                    {inv.role} · {inv.status} · expires {new Date(inv.expires_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {inv.status === 'Pending' && (
                    <>
                      <button onClick={() => copyInviteLink((inv as any).token || '', inv.id)}
                        disabled={!(inv as any).token}
                        style={{ background: 'var(--surface-hover)', border: '1px solid var(--surface-border)', borderRadius: '6px', padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: 'white', display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer' }}>
                        <Copy size={13} /> {copiedInviteId === inv.id ? 'Copied!' : 'Copy link'}
                      </button>
                      <button onClick={() => revokeInvite(inv.id)}
                        style={{ background: 'transparent', border: '1px solid var(--surface-border)', borderRadius: '6px', padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: '#f87171', cursor: 'pointer' }}>
                        Revoke
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
          <p style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', color: '#71717a', margin: 0 }}>
            Token-based invite links are only shown at creation time. Re-invite if lost.
          </p>
        </div>
      )}
    </div>
  );
}
