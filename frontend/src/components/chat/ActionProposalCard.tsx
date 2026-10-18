import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import type { ActionRecord } from '../../types/action';
import StatusBadge from '../common/StatusBadge';

export default function ActionProposalCard({
  action,
  busy,
  ticketId,
  onApprove,
  onReject,
  onExecute,
}: {
  action: ActionRecord;
  busy: boolean;
  ticketId: number | null;
  onApprove: () => void;
  onReject: () => void;
  onExecute: () => void;
}) {
  const heading = action.status === 'proposed' ? 'Action proposed' : action.status === 'approved' ? 'Approved · ready to execute' : action.status === 'executed' ? 'Action completed' : 'Action rejected';
  return (
    <div className="mt-2 overflow-hidden rounded-lg border-2 border-amber-300 bg-amber-50/50">
      <div className="flex items-center gap-2 bg-amber-100 px-3 py-2">
        <AlertTriangle size={15} className="text-amber-700" />
        <p className="text-xs font-bold uppercase tracking-wide text-amber-800">{heading}</p>
      </div>
      <div className="space-y-1.5 px-3 py-3 text-sm">
        <p className="font-semibold text-slate-900">Create Support Ticket</p>
        <p className="text-xs text-slate-600">
          <span className="font-medium">Action ID:</span> {action.id}
        </p>
        <p className="text-xs text-slate-600">
          <span className="font-medium">Customer ID:</span> {action.customer_id ?? '—'}
        </p>
        <p className="text-xs text-slate-600">
          <span className="font-medium">Title:</span> {action.title}
        </p>
        <p className="text-xs text-slate-600">
          <span className="font-medium">Description:</span> {action.description}
        </p>
        <p className="text-xs text-slate-600">
          <span className="font-medium">Reason:</span> {action.reason}
        </p>
        <div className="flex items-center gap-2 pt-1">
          <span className="text-xs text-slate-500">Status:</span>
          <StatusBadge value={action.status === 'proposed' ? 'Awaiting approval' : action.status} />
        </div>
        {action.status === 'proposed' && (
          <p className="rounded-md bg-white/70 px-2 py-1.5 text-[11px] leading-relaxed text-amber-800">
            The AI has proposed this action and the backend saved it. Nothing has been changed yet.
            Approval is required before execution.
          </p>
        )}
        {action.status === 'executed' && (
          <p className="flex items-center gap-1.5 text-xs font-medium text-green-700">
            <CheckCircle2 size={14} /> {ticketId ? `Ticket #${ticketId} created successfully.` : 'This action was executed successfully.'}
          </p>
        )}
        {action.status === 'rejected' && (
          <p className="flex items-center gap-1.5 text-xs font-medium text-red-700">
            <XCircle size={14} /> Rejected. No changes were made.
          </p>
        )}
        {action.status === 'proposed' && (
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              disabled={busy}
              onClick={onApprove}
              className="rounded-lg bg-green-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-800 disabled:opacity-50"
            >
              {busy ? 'Saving…' : 'Approve'}
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
        {action.status === 'approved' && <div className="pt-1"><p className="mb-2 text-xs text-emerald-800">Approved and ready. Execution is a separate step.</p><button type="button" disabled={busy} onClick={onExecute} className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-50">{busy ? 'Executing…' : 'Execute approved action'}</button></div>}
      </div>
    </div>
  );
}
