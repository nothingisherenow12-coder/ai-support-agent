import { useCallback, useEffect, useState } from 'react';
import PageContainer from '../components/layout/PageContainer';
import ActionCard from '../components/actions/ActionCard';
import EmptyState from '../components/common/EmptyState';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { approveAction, executeAction, listActions, rejectAction } from '../api/actions';
import type { ActionRecord } from '../types/action';
import { getApiErrorMessage } from '../api/errors';

type Filter = 'proposed' | 'all';

export default function Actions({ canManage = true }: { canManage?: boolean }) {
  const [filter, setFilter] = useState<Filter>('proposed');
  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [tickets, setTickets] = useState<Record<number, number>>({});

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setActions(await listActions());
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load actions.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function run(id: number, op: 'approve' | 'reject' | 'execute') {
    setBusyId(id);
    try {
      if (op === 'approve') await approveAction(id);
      if (op === 'reject') await rejectAction(id);
      if (op === 'execute') {
        const result = await executeAction(id);
        setTickets((prev) => ({ ...prev, [id]: result.ticket.id }));
      }
      await refresh();
    } catch (err) {
      setError(getApiErrorMessage(err, `Action could not be ${op}d.`));
    } finally {
      setBusyId(null);
    }
  }

  const visible = filter === 'proposed' ? actions.filter((a) => a.status === 'proposed') : actions;
  const pendingCount = actions.filter((a) => a.status === 'proposed').length;

  return (
    <PageContainer>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Approval Queue</h1>
          <p className="mt-1 text-sm text-slate-500">
            State-changing operations require explicit approval. The backend executes approved
            actions exactly once — rejected or unapproved actions never touch the database.
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border border-slate-200 bg-white p-1 text-xs font-medium">
          {(['proposed', 'all'] as Filter[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`rounded-md px-3 py-1.5 capitalize ${filter === f ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              {f === 'proposed' ? `Pending (${pendingCount})` : `All (${actions.length})`}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs leading-relaxed text-amber-800">
        Safety model: AI proposes → human approves → backend executes exactly once. {pendingCount} pending.
      </div>

      <div className="mt-4">
        {loading && <LoadingState message="Loading actions…" />}
        {error && !loading && <ErrorState message={error} onRetry={() => void refresh()} />}
        {!loading && !error && visible.length === 0 && (
          <EmptyState
            title={filter === 'proposed' ? 'No pending actions.' : 'No actions yet.'}
            hint="Ask the AI Assistant to create a ticket and the proposal will appear here for approval."
          />
        )}
        {!loading && !error && (
          <div className="space-y-3">
            {visible.map((a) => (
              <ActionCard
                key={a.id}
                action={a}
                busy={busyId === a.id}
                ticketId={tickets[a.id] ?? null}
                canManage={canManage}
                onApprove={() => void run(a.id, 'approve')}
                onReject={() => void run(a.id, 'reject')}
                onExecute={() => void run(a.id, 'execute')}
              />
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
