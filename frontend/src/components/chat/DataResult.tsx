import type { Customer, Ticket } from '../../types/customer';
import StatusBadge from '../common/StatusBadge';

export default function DataResult({
  title,
  customer,
  tickets,
  ticket,
}: {
  title: string;
  customer?: Customer | null;
  tickets?: Ticket[];
  ticket?: Ticket | null;
}) {
  return (
    <div className="mt-2 overflow-hidden rounded-lg border border-slate-200">
      <div className="bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700">{title}</div>
      <div className="divide-y divide-slate-100">
        {customer && (
          <div className="px-3 py-2 text-xs text-slate-600">
            <span className="font-semibold text-slate-800">{customer.name}</span> · {customer.email}
            {customer.company ? ` · ${customer.company}` : ''} · ID {customer.id}
          </div>
        )}
        {ticket && <TicketRow ticket={ticket} />}
        {(tickets ?? []).map((t) => (
          <TicketRow key={t.id} ticket={t} />
        ))}
        {(!tickets || tickets.length === 0) && !ticket && !customer && (
          <p className="px-3 py-2 text-xs text-slate-500">No records found.</p>
        )}
      </div>
    </div>
  );
}

function TicketRow({ ticket: t }: { ticket: Ticket }) {
  return (
          <div className="px-3 py-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-slate-800">#{t.id} {t.title}</span>
              <StatusBadge value={t.status} />
              <StatusBadge value={t.priority} />
            </div>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{t.description}</p>
          </div>
  );
}
