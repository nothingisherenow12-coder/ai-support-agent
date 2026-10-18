import { useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowRight, Bot, LockKeyhole } from 'lucide-react';
import { signIn } from '../api/auth';
import { getApiErrorMessage } from '../api/errors';

export default function SignIn({ onSignedIn }: { onSignedIn: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(username, password);
      onSignedIn();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Sign-in failed. Check the API connection and credentials.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-[#f5f7f8] lg:grid-cols-[1.1fr_.9fr]">
      <section className="relative hidden overflow-hidden bg-[#102c2a] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full border border-white/10" />
        <div className="absolute -right-8 -top-8 h-64 w-64 rounded-full border border-white/10" />
        <div className="relative flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[#c6f36b] text-[#102c2a]"><Bot /></span><span className="font-semibold tracking-tight">AI Support <span className="font-normal text-white/50">Operations</span></span></div>
        <div className="relative max-w-xl"><p className="mb-5 text-xs font-semibold uppercase tracking-[.22em] text-[#c6f36b]">Operations, made clear</p><h1 className="text-5xl font-semibold leading-[1.08] tracking-tight">Every support detail, in one place.</h1><p className="mt-6 max-w-md text-base leading-7 text-white/65">Find grounded answers, understand customer history, and move approved work forward with confidence.</p><div className="mt-10 flex gap-3 text-xs text-white/60"><span className="rounded-full border border-white/15 px-3 py-2">Knowledge grounded</span><span className="rounded-full border border-white/15 px-3 py-2">Actions controlled</span></div></div>
        <p className="relative text-xs text-white/35">AI Support Operations · Secure workspace</p>
      </section>
      <section className="flex items-center justify-center px-5 py-12">
        <form onSubmit={submit} className="w-full max-w-sm">
          <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#e8f3dd] text-[#315b38] lg:hidden"><Bot /></div>
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-[#63834a]">Workspace sign in</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[#182321]">Welcome back</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">Sign in with the account configured for this support workspace.</p>
          <label className="mt-8 block text-sm font-medium text-slate-700">Username<input autoComplete="username" required value={username} onChange={(e) => setUsername(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 outline-none transition focus:border-[#729552] focus:ring-4 focus:ring-[#729552]/10" /></label>
          <label className="mt-4 block text-sm font-medium text-slate-700">Password<div className="relative mt-2"><LockKeyhole size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" /><input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3.5 outline-none transition focus:border-[#729552] focus:ring-4 focus:ring-[#729552]/10" /></div></label>
          {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</p>}
          <button disabled={busy} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-[#173b34] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#245349] disabled:opacity-60">{busy ? 'Signing in…' : 'Sign in'}{!busy && <ArrowRight size={16} />}</button>
          <p className="mt-5 text-center text-xs text-slate-400">Your session expires automatically for security.</p>
        </form>
      </section>
    </main>
  );
}
