import { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, Search, Ticket as TicketIcon } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { listCustomers } from '../api/customers';
import { listTickets, updateTicket } from '../api/tickets';
import type { Customer, Ticket } from '../types/customer';
import { getApiErrorMessage } from '../api/errors';

const statuses = ['open', 'in_progress', 'resolved', 'closed'];
const priorities = ['low', 'medium', 'high', 'urgent'];

export default function Tickets({ canManage = true }: { canManage?: boolean }) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const customerNames = useMemo(() => new Map(customers.map((customer) => [customer.id, customer.name])), [customers]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ticketPage, customerPage] = await Promise.all([
        listTickets({ status: status || undefined, priority: priority || undefined, q: query.trim() || undefined, limit: 25, offset: page * 25 }),
        listCustomers('', 100, 0),
      ]);
      setTickets(ticketPage.items);
      setTotal(ticketPage.total);
      setCustomers(customerPage.items);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load tickets.'));
    } finally {
      setLoading(false);
    }
  }, [page, priority, query, status]);

  useEffect(() => { void refresh(); }, [refresh]);

  async function changeTicket(id: number, field: 'status' | 'priority', value: string) {
    setSavingId(id);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateTicket(id, { [field]: value });
      setTickets((rows) => rows.map((ticket) => ticket.id === id ? updated : ticket));
      setNotice(`Ticket #${id} updated.`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to update ticket.'));
    } finally {
      setSavingId(null);
    }
  }

  return <PageContainer>
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-[10px] font-semibold uppercase tracking-[.18em] text-[#739269]">Support operations</p><h1 className="mt-2 text-2xl font-semibold tracking-tight text-[#182321]">Ticket management</h1><p className="mt-2 text-sm text-slate-500">Review tickets and update their status or priority.</p></div>
      <div className="flex items-center gap-2 rounded-full border border-[#e3eae1] bg-white px-3 py-2 text-xs text-slate-500"><TicketIcon size={15} className="text-[#63834a]"/>{total} tickets</div>
    </div>
    <section className="mt-5 rounded-2xl border border-[#e5ebe5] bg-white p-4 md:p-5">
      <form onSubmit={(event) => { event.preventDefault(); if (page === 0) void refresh(); else setPage(0); }} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[minmax(200px,1fr)_180px_160px_auto]">
        <label className="text-xs font-medium text-slate-600">Search title<div className="relative mt-1.5"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tickets…" className="w-full rounded-lg border border-slate-300 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-emerald-700"/></div></label>
        <label className="text-xs font-medium text-slate-600">Status<select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm"><option value="">All statuses</option>{statuses.map((value) => <option key={value} value={value}>{value.replace('_', ' ')}</option>)}</select></label>
        <label className="text-xs font-medium text-slate-600">Priority<select value={priority} onChange={(event) => setPriority(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm"><option value="">All priorities</option>{priorities.map((value) => <option key={value}>{value}</option>)}</select></label>
        <button type="submit" disabled={loading} className="self-end inline-flex h-[42px] items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"><RefreshCw size={14} className={loading ? 'animate-spin' : ''}/>Refresh</button>
      </form>
    </section>
    {notice && <p role="status" className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-900">{notice}</p>}
    {error && <div className="mt-4"><ErrorState message={error} onRetry={() => void refresh()}/></div>}
    <section className="mt-4">
      {loading ? <LoadingState message="Loading tickets…"/> : !error && tickets.length === 0 ? <EmptyState title="No tickets match these filters." hint="Try clearing the status, priority, or search filters."/> : !error && <div className="space-y-3">{tickets.map((ticket) => <article key={ticket.id} className="rounded-2xl border border-[#e5ebe5] bg-white p-4 md:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0 flex-1"><p className="text-xs font-semibold text-[#739269]">Ticket #{ticket.id} · Customer #{ticket.customer_id}{customerNames.has(ticket.customer_id) ? ` · ${customerNames.get(ticket.customer_id)}` : ''}</p><h2 className="mt-1 text-base font-semibold text-slate-900">{ticket.title}</h2><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{ticket.description}</p>{ticket.created_at && <p className="mt-3 text-xs text-slate-400">Created {new Date(ticket.created_at).toLocaleString()}</p>}</div>{canManage && <div className="flex gap-2"><label className="sr-only" htmlFor={`status-${ticket.id}`}>Status for ticket {ticket.id}</label><select id={`status-${ticket.id}`} value={ticket.status} disabled={savingId === ticket.id} onChange={(event) => void changeTicket(ticket.id, 'status', event.target.value)} className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs capitalize"><option value={ticket.status}>{ticket.status.replace('_', ' ')}</option>{statuses.filter((value) => value !== ticket.status).map((value) => <option key={value} value={value}>{value.replace('_', ' ')}</option>)}</select><label className="sr-only" htmlFor={`priority-${ticket.id}`}>Priority for ticket {ticket.id}</label><select id={`priority-${ticket.id}`} value={ticket.priority} disabled={savingId === ticket.id} onChange={(event) => void changeTicket(ticket.id, 'priority', event.target.value)} className="rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs capitalize"><option value={ticket.priority}>{ticket.priority}</option>{priorities.filter((value) => value !== ticket.priority).map((value) => <option key={value} value={value}>{value}</option>)}</select></div>}</div></article>)}</div>}
      {total > 25 && !loading && !error && <div className="mt-4 flex items-center justify-between text-xs text-slate-500"><span>Showing {page * 25 + 1}–{Math.min((page + 1) * 25, total)} of {total}</span><div className="flex gap-2"><button type="button" disabled={page === 0} onClick={() => setPage((value) => value - 1)} className="rounded border px-3 py-1.5 disabled:opacity-40">Previous</button><button type="button" disabled={(page + 1) * 25 >= total} onClick={() => setPage((value) => value + 1)} className="rounded border px-3 py-1.5 disabled:opacity-40">Next</button></div></div>}
    </section>
  </PageContainer>;
}
