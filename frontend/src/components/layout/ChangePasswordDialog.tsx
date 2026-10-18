import { useState, type FormEvent } from 'react';
import { changePassword } from '../../api/auth';
import { getApiErrorMessage } from '../../api/errors';

export default function ChangePasswordDialog({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null);
    if (next !== confirm) { setError('The new passwords do not match.'); return; }
    setBusy(true);
    try { await changePassword(current, next); setDone(true); setCurrent(''); setNext(''); setConfirm(''); }
    catch (err) { setError(getApiErrorMessage(err, 'Unable to change password.')); }
    finally { setBusy(false); }
  }

  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section role="dialog" aria-modal="true" aria-labelledby="change-password-title" className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
      <h2 id="change-password-title" className="text-lg font-semibold text-slate-900">Change password</h2>
      {done ? <><p role="status" className="mt-3 text-sm text-emerald-800">Password changed. Other active sessions have been signed out.</p><button type="button" onClick={onClose} className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Done</button></> : <form onSubmit={(event) => void submit(event)}>
        <p className="mt-1 text-xs text-slate-500">Use at least 12 characters. Changing it signs out your other sessions.</p>
        <label className="mt-4 block text-xs font-medium text-slate-600">Current password<input required autoComplete="current-password" type="password" value={current} onChange={(event) => setCurrent(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"/></label>
        <label className="mt-3 block text-xs font-medium text-slate-600">New password<input required minLength={12} autoComplete="new-password" type="password" value={next} onChange={(event) => setNext(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"/></label>
        <label className="mt-3 block text-xs font-medium text-slate-600">Confirm new password<input required minLength={12} autoComplete="new-password" type="password" value={confirm} onChange={(event) => setConfirm(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"/></label>
        {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
        <div className="mt-5 flex justify-end gap-2"><button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600">Cancel</button><button disabled={busy} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy ? 'Saving…' : 'Change password'}</button></div>
      </form>}
    </section>
  </div>;
}
