import type { ChatMessage as ChatMessageType } from '../../types/chat';
import type { ActionRecord } from '../../types/action';
import ActionProposalCard from './ActionProposalCard';
import DataResult from './DataResult';
import SourceList from './SourceList';

export default function ChatMessage({
  message,
  action,
  busy,
  ticketId,
  onApprove,
  onReject,
  onExecute,
}: {
  message: ChatMessageType;
  action?: ActionRecord | null;
  busy: boolean;
  ticketId: number | null;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  onExecute: (id: number) => void;
}) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${
          isUser ? 'bg-slate-900 text-white' : 'border border-slate-200 bg-white text-slate-800'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
        {!isUser && message.content?.kind === 'knowledge' && (
          <SourceList response={message.content.response} />
        )}
        {!isUser && message.content?.kind === 'data' && (
          <DataResult
            title={message.content.title}
            customer={message.content.customer}
            tickets={message.content.tickets}
            ticket={message.content.ticket}
          />
        )}
        {!isUser && message.content?.kind === 'action' && action && (
          <ActionProposalCard
            action={action}
            busy={busy}
            ticketId={ticketId}
            onApprove={() => onApprove(action.id)}
            onReject={() => onReject(action.id)}
            onExecute={() => onExecute(action.id)}
          />
        )}
        {!isUser && message.content?.kind === 'error' && (
          <p className="mt-1 text-xs text-red-600">{message.content.message}</p>
        )}
      </div>
    </div>
  );
}
