import type { Ticket } from '../../types/customer';
import StatusBadge from '../common/StatusBadge';
import EmptyState from '../common/EmptyState';

export default function TicketList({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return <EmptyState title="No tickets found." hint="This customer has no tickets in the system." />;
  }
  return (
    <div className="space-y-2">
      {tickets.map((t) => (
        <div key={t.id} className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">#{t.id} {t.title}</span>
            <StatusBadge value={t.status} />
            <StatusBadge value={t.priority} />
          </div>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{t.description}</p>
          <p className="mt-1 text-xs text-slate-400">Customer ID {t.customer_id}</p>
        </div>
      ))}
    </div>
  );
}
