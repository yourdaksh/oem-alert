'use client';
/**
 * Global scan state shared across the dashboard.
 *
 * Lives in the dashboard layout (not on the Manual Scan page) so scans keep
 * running when the user navigates away. Pages consume `useScan()`; the banner
 * reads the same context. A snapshot is also mirrored to localStorage so the
 * banner can hint at progress if the provider hasn't mounted yet.
 */
import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from 'react';
import { getSupabase, API_URL } from '../../lib/supabase';

export type OemEntry = { id: string; name: string; description: string; enabled: boolean };
export type ScanLog = {
  oem_name: string; scan_type: string; status: string;
  vulnerabilities_found: number; new_vulnerabilities: number;
  error_message: string | null; scan_date: string;
};
export type RunResult = {
  oem: string;
  status: 'running' | 'ok' | 'error';
  found?: number;
  new?: number;
  error?: string;
  finishedAt?: number;
};

type ScanCtx = {
  loading: boolean;
  error: string | null;
  role: string;
  oems: OemEntry[];
  logs: ScanLog[];
  running: Record<string, RunResult>;
  runningAll: boolean;
  startedAt: number | null;
  lastByOem: Record<string, ScanLog>;
  summary: { ok: number; failed: number; running: number; found: number; new: number };
  scanOne: (oemId: string) => Promise<void>;
  scanAll: () => Promise<void>;
  refresh: () => Promise<void>;
  clearResults: () => void;
  isOwner: boolean;
};

const Ctx = createContext<ScanCtx | null>(null);

const BANNER_KEY = 'oem-alert.scan';
// Generous client cap. Some OEMs (Android, Apple, Microsoft) legitimately take
// 60-120s. Cutting them off at 90s was flagging real scans as "timed out".
const PER_OEM_TIMEOUT_MS = 180_000;
// 6 parallel workers. FastAPI's default threadpool is 40 so the API is fine;
// the limit now is the slowest OEM in each batch, not queue depth.
const CONCURRENCY = 6;

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await getSupabase().auth.getSession();
  return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
}

function writeBanner(state: null | {
  running: boolean; total: number; completed: number; failed: number;
  startedAt: number; lastOem?: string | null;
}) {
  if (typeof window === 'undefined') return;
  if (!state) window.localStorage.removeItem(BANNER_KEY);
  else window.localStorage.setItem(BANNER_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent('oem-alert-scan-change'));
}

export function ScanProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string>('');
  const [oems, setOems] = useState<OemEntry[]>([]);
  const [logs, setLogs] = useState<ScanLog[]>([]);
  const [running, setRunning] = useState<Record<string, RunResult>>({});
  const [runningAll, setRunningAll] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  // Ref mirrors of running/runningAll so the scanAll worker loop can read the
  // latest state without adding every update to its dependency list.
  const runningRef = useRef(running);
  runningRef.current = running;
  const runningAllRef = useRef(runningAll);
  runningAllRef.current = runningAll;
  const oemsRef = useRef(oems);
  oemsRef.current = oems;

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const headers = await authHeaders();
      const [oemsRes, logsRes, membersRes, userRes] = await Promise.all([
        fetch(`${API_URL}/scrapers/oems`, { headers }),
        fetch(`${API_URL}/scrapers/status?limit=60`, { headers }),
        fetch(`${API_URL}/organizations/members`, { headers }),
        getSupabase().auth.getUser(),
      ]);
      if (oemsRes.ok) setOems(await oemsRes.json());
      else if (oemsRes.status !== 403) {
        // 403 just means this user isn't an owner — not an error worth shouting about
        throw new Error((await oemsRes.json()).detail || 'Failed to load scanners');
      }
      if (logsRes.ok) setLogs(await logsRes.json());
      if (membersRes.ok) {
        const members = await membersRes.json();
        const me = members.find((m: any) => m.id === userRes.data.user?.id);
        setRole(me?.role || '');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const scanOne = useCallback(async (oemId: string) => {
    // Avoid double-starting the same OEM if the user mashes buttons
    if (runningRef.current[oemId]?.status === 'running') return;

    setRunning(p => ({ ...p, [oemId]: { oem: oemId, status: 'running' } }));
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), PER_OEM_TIMEOUT_MS);
    try {
      const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
      const res = await fetch(`${API_URL}/scrapers/run-one/${oemId}`, {
        method: 'POST', headers, signal: controller.signal,
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload.detail || `Scrape failed (${res.status})`);
      setRunning(p => ({
        ...p,
        [oemId]: { oem: oemId, status: 'ok', found: payload.found, new: payload.new, finishedAt: Date.now() },
      }));
    } catch (e: any) {
      const msg = e.name === 'AbortError'
        ? `Timed out after ${Math.round(PER_OEM_TIMEOUT_MS / 1000)}s — the OEM source is slow. Try again.`
        : (e.message || 'Scrape failed');
      setRunning(p => ({
        ...p,
        [oemId]: { oem: oemId, status: 'error', error: msg, finishedAt: Date.now() },
      }));
    } finally {
      clearTimeout(timer);
    }
  }, []);

  const scanAll = useCallback(async () => {
    if (runningAllRef.current) return;
    const started = Date.now();
    setStartedAt(started);
    setRunningAll(true);
    // Keep prior results visible but reset so the progress counter is fresh
    setRunning({});

    const enabledOems = oemsRef.current.filter(x => x.enabled);
    const queue = enabledOems.map(o => o.id);
    const total = queue.length;

    writeBanner({ running: true, total, completed: 0, failed: 0, startedAt: started, lastOem: null });

    const worker = async () => {
      while (queue.length) {
        const id = queue.shift();
        if (!id) return;
        writeBanner({
          running: true,
          total,
          completed: Object.values(runningRef.current).filter(r => r.status === 'ok').length,
          failed: Object.values(runningRef.current).filter(r => r.status === 'error').length,
          startedAt: started,
          lastOem: oemsRef.current.find(o => o.id === id)?.name ?? id,
        });
        await scanOne(id);
      }
    };
    await Promise.all(Array.from({ length: CONCURRENCY }, worker));

    writeBanner(null);
    setRunningAll(false);
    // Refresh logs so "last scan" timestamps update in the UI
    await refresh();
  }, [scanOne, refresh]);

  const clearResults = useCallback(() => setRunning({}), []);

  const lastByOem = useMemo(() => {
    const m: Record<string, ScanLog> = {};
    for (const l of logs) {
      const k = l.oem_name.toLowerCase();
      if (!m[k]) m[k] = l;
    }
    return m;
  }, [logs]);

  const summary = useMemo(() => {
    return Object.values(running).reduce(
      (acc, r) => {
        if (r.status === 'ok') {
          acc.found += r.found || 0;
          acc.new += r.new || 0;
          acc.ok += 1;
        } else if (r.status === 'error') acc.failed += 1;
        else if (r.status === 'running') acc.running += 1;
        return acc;
      },
      { ok: 0, failed: 0, running: 0, found: 0, new: 0 }
    );
  }, [running]);

  const isOwner = role === 'Owner' || role === 'Admin';

  const value: ScanCtx = {
    loading, error, role, oems, logs, running, runningAll, startedAt,
    lastByOem, summary, scanOne, scanAll, refresh, clearResults, isOwner,
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useScan(): ScanCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useScan must be used within ScanProvider');
  return v;
}
