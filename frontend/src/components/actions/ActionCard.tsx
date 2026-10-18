import { ShieldAlert } from 'lucide-react';
import type { ActionRecord } from '../../types/action';
import StatusBadge from '../common/StatusBadge';

export default function ActionCard({
  action,
  busy,
  ticketId,
  canManage = true,
  onApprove,
  onReject,
  onExecute,
}: {
  action: ActionRecord;
  busy: boolean;
  ticketId?: number | null;
  canManage?: boolean;
  onApprove: () => void;
  onReject: () => void;
  onExecute: () => void;
}) {
  const pending = action.status === 'proposed';
  const approved = action.status === 'approved';

  return (
    <div className={`rounded-xl border bg-white p-4 ${pending ? 'border-amber-300' : 'border-slate-200'}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-sm font-bold text-slate-900">
          {pending && <ShieldAlert size={16} className="text-amber-600" />}
          {action.action_type === 'create_ticket' ? 'Create Support Ticket' : action.action_type}
          <span className="font-normal text-slate-400">#{action.id}</span>
        </p>
        <StatusBadge value={action.status} />
      </div>
      <dl className="mt-3 space-y-1 text-xs text-slate-600">
        <div className="flex gap-2"><dt className="w-20 shrink-0 font-medium text-slate-500">Customer</dt><dd>ID {action.customer_id ?? '—'}</dd></div>
        <div className="flex gap-2"><dt className="w-20 shrink-0 font-medium text-slate-500">Title</dt><dd>{action.title}</dd></div>
        <div className="flex gap-2"><dt className="w-20 shrink-0 font-medium text-slate-500">Description</dt><dd>{action.description}</dd></div>
        <div className="flex gap-2"><dt className="w-20 shrink-0 font-medium text-slate-500">Reason</dt><dd>{action.reason}</dd></div>
        <div className="flex gap-2"><dt className="w-20 shrink-0 font-medium text-slate-500">Created</dt><dd>{new Date(action.created_at).toLocaleString()}</dd></div>
      </dl>
      {canManage && pending && (
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={onApprove}
            className="rounded-lg bg-green-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-800 disabled:opacity-50"
          >
            {busy ? 'Working…' : 'Approve'}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onReject}
            className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}
      {canManage && approved && (
        <div className="mt-3">
          <button
            type="button"
            disabled={busy}
            onClick={onExecute}
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {busy ? 'Executing…' : 'Execute approved action'}
          </button>
        </div>
      )}
      {action.status === 'executed' && (
        <p className="mt-3 text-xs text-green-700">
          Executed.{ticketId ? ` Ticket #${ticketId} created.` : ' Ticket created.'}
        </p>
      )}
      {action.status === 'rejected' && (
        <p className="mt-3 text-xs text-slate-500">Rejected. No changes were made.</p>
      )}
    </div>
  );
}
