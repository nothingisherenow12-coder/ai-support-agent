import { NavLink, useLocation } from 'react-router-dom';
import { Bot, FileText, KeyRound, LayoutDashboard, LogOut, ShieldCheck, Ticket, Users } from 'lucide-react';
import { signOut as endSession } from '../../api/auth';
import type { WorkspaceSession } from '../../api/auth';
import { useState } from 'react';
import ChangePasswordDialog from './ChangePasswordDialog';

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/assistant', label: 'Assistant', icon: Bot },
  { to: '/knowledge', label: 'Knowledge', icon: FileText },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/tickets', label: 'Tickets', icon: Ticket },
  { to: '/actions', label: 'Approvals', icon: ShieldCheck },
];
const names: Record<string, string> = { '/': 'Overview', '/assistant': 'AI assistant', '/knowledge': 'Knowledge base', '/customers': 'Customers', '/tickets': 'Ticket management', '/actions': 'Approval queue' };

export default function Header({ session }: { session: WorkspaceSession }) {
  const location = useLocation();
  const [changingPassword, setChangingPassword] = useState(false);
  function logout() {
    void endSession().finally(() => window.dispatchEvent(new Event('support-agent:session-expired')));
  }
  const visibleLinks = [...links.filter((link) => session.role !== 'viewer' || link.to !== '/assistant'), ...(session.role === 'admin' ? [{ to: '/team', label: 'Team', icon: Users }] : [])];
  return <><header className="sticky top-0 z-20 border-b border-[#e7ece8] bg-[#fbfcfa]/95 backdrop-blur"><div className="flex h-[76px] items-center justify-between px-5 md:px-8"><div><p className="text-[10px] font-semibold uppercase tracking-[.17em] text-[#7c8a80]">Support workspace</p><h1 className="mt-1 text-base font-semibold tracking-tight text-[#182321]">{names[location.pathname] ?? 'Support workspace'}</h1></div><div className="flex items-center gap-2 sm:gap-3"><div className="hidden rounded-full border border-[#e5ebe5] bg-white px-3 py-2 text-[11px] text-[#59705f] sm:block">{session.username} · {session.role}</div><button type="button" onClick={() => setChangingPassword(true)} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900" aria-label="Change password"><KeyRound size={15}/><span className="hidden sm:inline">Password</span></button><button type="button" onClick={logout} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900" aria-label="Sign out"><LogOut size={15}/><span className="hidden sm:inline">Sign out</span></button></div></div><nav aria-label="Main navigation" className="flex gap-1 overflow-x-auto px-3 pb-3 md:hidden">{visibleLinks.map(({to,label,icon:Icon,end})=><NavLink key={to} to={to} end={end} className={({isActive})=>`flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium transition ${isActive?'bg-[#173b34] text-white':'text-slate-500 hover:bg-slate-100'}`}><Icon size={14}/>{label}</NavLink>)}</nav></header>{changingPassword && <ChangePasswordDialog onClose={() => setChangingPassword(false)} />}</>;
}
