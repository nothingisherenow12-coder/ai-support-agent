import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { UserPlus, Users } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import ErrorState from '../components/common/ErrorState';
import LoadingState from '../components/common/LoadingState';
import { createUser, listAuditEvents, listUsers, updateUser, type AuditEvent, type WorkspaceUser } from '../api/admin';
import { getApiErrorMessage } from '../api/errors';

export default function TeamAdmin() {
  const [users, setUsers] = useState<WorkspaceUser[]>([]);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<WorkspaceUser['role']>('agent');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [resetId, setResetId] = useState<number | null>(null);
  const [resetPassword, setResetPassword] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [userRows, auditRows] = await Promise.all([listUsers(), listAuditEvents()]);
      setUsers(userRows); setEvents(auditRows);
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to load team and audit records.')); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null); setNotice(null);
    try {
      const created = await createUser({ username: username.trim(), password, role });
      setUsername(''); setPassword(''); setRole('agent');
      setNotice(`User ${created.username} was created.`);
      await refresh();
    } catch (err) { setError(getApiErrorMessage(err, 'Unable to create user.')); }
  }

  async function changeUser(user: WorkspaceUser, changes: { role?: WorkspaceUser['role']; is_active?: boolean; password?: string }) {
    setBusyId(user.id); setError(null); setNotice(null);
    try { await updateUser(user.id, changes); setNotice(changes.password ? `Reset the password for ${user.username}. Their other sessions are signed out.` : `Updated ${user.username}.`); setResetId(null); setResetPassword(''); await refresh(); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to update user.')); }
    finally { setBusyId(null); }
  }

  return <PageContainer>
    <div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-[#e9f1ef] text-[#37685e]"><Users size={20}/></span><div><h1 className="text-2xl font-semibold tracking-tight text-[#182321]">Team &amp; audit</h1><p className="mt-1 text-sm text-slate-500">Manage workspace accounts and review recorded changes.</p></div></div>
    {error && <div className="mt-4"><ErrorState message={error} onRetry={() => void refresh()}/></div>}
    {notice && <p role="status" className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-900">{notice}</p>}
    <section className="mt-6 rounded-2xl border border-[#e5ebe5] bg-white p-5"><h2 className="text-sm font-semibold text-slate-900">Add a workspace user</h2><p className="mt-1 text-xs text-slate-500">Passwords need at least 12 characters. Share them securely.</p><form onSubmit={submit} className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_180px_auto]"><label className="text-xs font-medium text-slate-600">Username<input required minLength={3} pattern="[A-Za-z0-9_.-]+" autoComplete="off" value={username} onChange={(e) => setUsername(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"/></label><label className="text-xs font-medium text-slate-600">Temporary password<input required minLength={12} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"/></label><label className="text-xs font-medium text-slate-600">Role<select value={role} onChange={(e) => setRole(e.target.value as WorkspaceUser['role'])} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm"><option value="agent">Agent</option><option value="viewer">Viewer</option><option value="admin">Admin</option></select></label><button className="self-end inline-flex h-[42px] items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 text-sm font-medium text-white"><UserPlus size={15}/>Create user</button></form></section>
    {loading ? <div className="mt-5"><LoadingState message="Loading team records…"/></div> : <>
      <section className="mt-6"><h2 className="mb-3 text-sm font-semibold text-slate-900">Workspace users ({users.length})</h2><div className="space-y-2">{users.map((user) => <article key={user.id} className="rounded-xl border border-[#e5ebe5] bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm font-semibold text-slate-800">{user.username}</p><p className="mt-1 text-xs text-slate-500">Created {new Date(user.created_at).toLocaleString()} · {user.is_active ? 'Active' : 'Disabled'}</p></div><div className="flex items-center gap-2"><select aria-label={`Role for ${user.username}`} disabled={busyId === user.id} value={user.role} onChange={(e) => void changeUser(user, { role: e.target.value as WorkspaceUser['role'] })} className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs"><option value="admin">Admin</option><option value="agent">Agent</option><option value="viewer">Viewer</option></select><button type="button" disabled={busyId === user.id} onClick={() => void changeUser(user, { is_active: !user.is_active })} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-50">{user.is_active ? 'Disable' : 'Enable'}</button><button type="button" onClick={() => { setResetId(resetId === user.id ? null : user.id); setResetPassword(''); }} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700">Reset password</button></div></div>{resetId === user.id && <form onSubmit={(event) => { event.preventDefault(); if (resetPassword.length >= 12) void changeUser(user, { password: resetPassword }); }} className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3"><label className="sr-only" htmlFor={`reset-password-${user.id}`}>New temporary password for {user.username}</label><input id={`reset-password-${user.id}`} required minLength={12} autoComplete="new-password" type="password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} placeholder="New temporary password" className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs"/><button type="submit" disabled={busyId === user.id} className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">{busyId === user.id ? 'Saving…' : 'Set password'}</button></form>}</article>)}</div></section>
      <section className="mt-8"><div className="mb-3"><h2 className="text-sm font-semibold text-slate-900">Audit log</h2><p className="mt-1 text-xs text-slate-500">Latest 200 recorded workspace changes.</p></div><div className="overflow-hidden rounded-xl border border-[#e5ebe5] bg-white">{events.length === 0 ? <p className="p-4 text-sm text-slate-500">No events recorded yet.</p> : events.map((event) => <div key={event.id} className="flex flex-wrap justify-between gap-2 border-b border-slate-100 px-4 py-3 last:border-0"><div><p className="text-sm font-medium text-slate-800">{event.event_type.replace(/\\./g, ' ')}</p><p className="mt-1 text-xs text-slate-500">{event.actor_username} · {event.entity_type} {event.entity_id ?? ''}</p></div><time className="text-xs text-slate-400">{new Date(`${event.created_at}Z`).toLocaleString()}</time></div>)}</div></section>
    </>}
  </PageContainer>;
}
