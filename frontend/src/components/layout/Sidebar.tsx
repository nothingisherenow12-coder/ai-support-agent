import { NavLink } from 'react-router-dom';
import { Bot, FileText, LayoutDashboard, ShieldCheck, Ticket, Users, UserCog } from 'lucide-react';

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/assistant', label: 'AI assistant', icon: Bot },
  { to: '/knowledge', label: 'Knowledge base', icon: FileText },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/tickets', label: 'Tickets', icon: Ticket },
  { to: '/actions', label: 'Approvals', icon: ShieldCheck },
];

export default function Sidebar({ isAdmin, canOperate }: { isAdmin: boolean; canOperate: boolean }) {
  return (
    <aside className="hidden w-[250px] shrink-0 flex-col bg-[#102c2a] text-white md:flex">
      <div className="flex h-[76px] items-center gap-3 border-b border-white/10 px-6"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#c6f36b] text-[#102c2a]"><Bot size={19} /></span><div><p className="text-sm font-semibold tracking-tight">AI Support</p><p className="text-[11px] text-white/45">Operations console</p></div></div>
      <p className="px-6 pb-2 pt-8 text-[10px] font-semibold uppercase tracking-[.18em] text-white/35">Workspace</p>
      <nav className="flex flex-col gap-1 px-3">
        {[...links.filter((link) => canOperate || link.to !== '/assistant'), ...(isAdmin ? [{ to: '/team', label: 'Team & audit', icon: UserCog }] : [])].map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-medium transition ${isActive ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/5 hover:text-white'}`}><Icon size={17} strokeWidth={1.8} /><span className="flex-1">{label}</span></NavLink>)}
      </nav>
      <div className="mt-auto p-4"><div className="rounded-2xl border border-white/10 bg-white/[.04] p-4"><div className="flex items-center gap-2 text-xs font-semibold text-[#c6f36b]"><ShieldCheck size={15} /> Controlled actions</div><p className="mt-2 text-[11px] leading-5 text-white/50">Review each proposal. Approve it, then execute it as a separate step.</p></div><p className="px-2 pt-4 text-[10px] text-white/30">NORTHSTAR · SUPPORT CONSOLE</p></div>
    </aside>
  );
}
