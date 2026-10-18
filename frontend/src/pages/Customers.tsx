import { useEffect, useState, type FormEvent } from 'react';
import { Search, UserPlus } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import CustomerSearch from '../components/customers/CustomerSearch';
import CustomerCard from '../components/customers/CustomerCard';
import TicketList from '../components/customers/TicketList';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { createCustomer, getCustomer, getCustomerTickets, listCustomers } from '../api/customers';
import type { Customer, Ticket } from '../types/customer';
import { getApiErrorMessage } from '../api/errors';
import BulkImport from '../components/customers/BulkImport';

export default function Customers({ canManage = true }: { canManage?: boolean }) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketTotal, setTicketTotal] = useState(0);
  const [ticketPage, setTicketPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [lastSearchedId, setLastSearchedId] = useState<number | null>(null);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newCompany, setNewCompany] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createdNotice, setCreatedNotice] = useState<string | null>(null);
  const [directoryRows, setDirectoryRows] = useState<Customer[]>([]);
  const [directoryTotal, setDirectoryTotal] = useState(0);
  const [directoryPage, setDirectoryPage] = useState(0);
  const [directoryQuery, setDirectoryQuery] = useState('');
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [directoryError, setDirectoryError] = useState<string | null>(null);

  async function searchDirectory(query = directoryQuery, page = directoryPage) {
    setDirectoryLoading(true);
    setDirectoryError(null);
    try {
      const result = await listCustomers(query, 25, page * 25);
      setDirectoryRows(result.items);
      setDirectoryTotal(result.total);
    }
    catch (err) { setDirectoryError(getApiErrorMessage(err, 'Unable to load customer directory.')); }
    finally { setDirectoryLoading(false); }
  }

  useEffect(() => { void searchDirectory(); }, [directoryPage]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    setError(null);
    setCreateError(null);
    setCreatedNotice(null);
    try {
      const created = await createCustomer({
        name: newName.trim(),
        email: newEmail.trim(),
        company: newCompany.trim() || null,
      });
      setCustomer(created);
      setDirectoryRows((rows) => [created, ...rows.filter((row) => row.id !== created.id)].slice(0, 25));
      setDirectoryTotal((total) => total + 1);
      setTickets([]);
      setTicketTotal(0);
      setSearched(true);
      setLastSearchedId(created.id);
      setNewName('');
      setNewEmail('');
      setNewCompany('');
      setCreatedNotice(`Customer ${created.name} was added as #${created.id}.`);
    } catch (err) {
      setCreateError(getApiErrorMessage(err, 'Unable to add customer.'));
    } finally {
      setCreating(false);
    }
  }

  async function handleSearch(id: number, page = ticketPage) {
    setTicketPage(page);
    setLoading(true);
    setError(null);
    setSearched(true);
    setLastSearchedId(id);
    try {
      const [c, ticketResult] = await Promise.all([getCustomer(id), getCustomerTickets(id, 25, page * 25)]);
      setCustomer(c);
      setTickets(ticketResult.items);
      setTicketTotal(ticketResult.total);
    } catch (err) {
      setCustomer(null);
      setTickets([]);
      setTicketTotal(0);
      setError(getApiErrorMessage(err, 'Unable to load customer.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageContainer>
      <h1 className="text-xl font-bold text-slate-900">Customers &amp; Tickets</h1>
      <p className="mt-1 text-sm text-slate-500">
        Add a customer or search an existing profile and its support tickets.
      </p>

      {canManage && <section className="mt-5 rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
        <div className="mb-4 flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-emerald-50 text-emerald-800"><UserPlus size={17}/></span>
          <div><h2 className="text-sm font-semibold text-slate-900">Add a customer</h2><p className="mt-0.5 text-xs text-slate-500">Name and a unique email are required.</p></div>
        </div>
        <form onSubmit={handleCreate} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="text-xs font-medium text-slate-600">Name<input required minLength={2} maxLength={255} value={newName} onChange={(e) => setNewName(e.target.value)} autoComplete="name" placeholder="Alex Morgan" className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-700"/></label>
          <label className="text-xs font-medium text-slate-600">Email<input required type="email" maxLength={255} value={newEmail} onChange={(e) => setNewEmail(e.target.value)} autoComplete="email" placeholder="alex@example.com" className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-700"/></label>
          <label className="text-xs font-medium text-slate-600">Company <span className="font-normal text-slate-400">(optional)</span><input maxLength={255} value={newCompany} onChange={(e) => setNewCompany(e.target.value)} autoComplete="organization" placeholder="Acme Inc" className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-700"/></label>
          <button type="submit" disabled={creating || !newName.trim() || !newEmail.trim()} className="self-end inline-flex h-[42px] items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">{creating ? 'Adding…' : <><UserPlus size={15}/>Add customer</>}</button>
        </form>
        {createError && <p role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{createError}</p>}
        {createdNotice && <p role="status" className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">{createdNotice}</p>}
      </section>}
      {canManage && <BulkImport kind="customers" onImported={() => { setDirectoryPage(0); void searchDirectory(directoryQuery, 0); }} />}
      {canManage && <BulkImport kind="tickets" onImported={() => { if (customer) void handleSearch(customer.id); }} />}

      <section className="mt-5 rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
        <div className="mb-3"><h2 className="text-sm font-semibold text-slate-900">Customer directory</h2><p className="mt-1 text-xs text-slate-500">Search by name, email, or company.</p></div>
        <form onSubmit={(event) => { event.preventDefault(); setDirectoryPage(0); void searchDirectory(directoryQuery, 0); }} className="flex gap-2"><input value={directoryQuery} onChange={(event) => setDirectoryQuery(event.target.value)} placeholder="Search customers…" aria-label="Search customers by name, email, or company" className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-700"/><button type="submit" disabled={directoryLoading} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"><Search size={15}/>{directoryLoading ? 'Searching…' : 'Search'}</button></form>
        {directoryError && <p role="alert" className="mt-3 text-sm text-red-700">{directoryError}</p>}
        {!directoryError && !directoryLoading && directoryRows.length === 0 && <p className="mt-3 text-sm text-slate-500">No customers found.</p>}
        {directoryRows.length > 0 && <div className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-100">{directoryRows.map((row) => <div key={row.id} className="flex items-center justify-between gap-3 px-3 py-2.5"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">{row.name} <span className="font-normal text-slate-400">#{row.id}</span></p><p className="truncate text-xs text-slate-500">{row.email}{row.company ? ` · ${row.company}` : ''}</p></div><button type="button" disabled={loading} onClick={() => void handleSearch(row.id, 0)} className="shrink-0 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50">View</button></div>)}</div>}
        {directoryTotal > 25 && <div className="mt-3 flex items-center justify-between text-xs text-slate-500"><span>Showing {directoryPage * 25 + 1}–{Math.min((directoryPage + 1) * 25, directoryTotal)} of {directoryTotal}</span><div className="flex gap-2"><button type="button" disabled={directoryPage === 0 || directoryLoading} onClick={() => setDirectoryPage((page) => page - 1)} className="rounded border px-3 py-1.5 disabled:opacity-40">Previous</button><button type="button" disabled={(directoryPage + 1) * 25 >= directoryTotal || directoryLoading} onClick={() => setDirectoryPage((page) => page + 1)} className="rounded border px-3 py-1.5 disabled:opacity-40">Next</button></div></div>}
      </section>

      <div className="mt-5">
        <h2 className="mb-2 text-sm font-semibold text-slate-800">Find an existing customer</h2>
        <CustomerSearch onSearch={(id) => { void handleSearch(id, 0); }} loading={loading} />
      </div>

      <div className="mt-3">
        {loading && <LoadingState message="Loading customer…" />}
        {error && !loading && <ErrorState message={error} onRetry={() => { if (lastSearchedId !== null) void handleSearch(lastSearchedId); }} />}
      </div>

      {!loading && !error && !searched && (
        <div className="mt-3">
          <EmptyState title="Search for a customer" hint="Enter a customer ID above to load their profile and tickets." />
        </div>
      )}

      {!loading && !error && customer && (
        <div className="mt-4 space-y-4">
          <CustomerCard customer={customer} />
          <div>
            <h2 className="mb-2 text-sm font-bold text-slate-900">Tickets ({ticketTotal})</h2>
            <TicketList tickets={tickets} />
            {ticketTotal > 25 && <div className="mt-3 flex items-center justify-between text-xs text-slate-500"><span>Showing {ticketPage * 25 + 1}–{Math.min((ticketPage + 1) * 25, ticketTotal)} of {ticketTotal}</span><div className="flex gap-2"><button type="button" disabled={ticketPage === 0 || loading} onClick={() => { const next = ticketPage - 1; setTicketPage(next); if (customer) void handleSearch(customer.id, next); }} className="rounded border px-3 py-1.5 disabled:opacity-40">Previous</button><button type="button" disabled={(ticketPage + 1) * 25 >= ticketTotal || loading} onClick={() => { const next = ticketPage + 1; setTicketPage(next); if (customer) void handleSearch(customer.id, next); }} className="rounded border px-3 py-1.5 disabled:opacity-40">Next</button></div></div>}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
