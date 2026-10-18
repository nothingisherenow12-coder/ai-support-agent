import { useEffect, useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/chat';
import type { ActionRecord } from '../../types/action';
import ChatMessage from './ChatMessage';

export default function ChatWindow({
  messages,
  thinking,
  actionsById,
  ticketsByActionId,
  busyActionId,
  onApprove,
  onReject,
  onExecute,
}: {
  messages: ChatMessageType[];
  thinking: boolean;
  actionsById: Record<number, ActionRecord>;
  ticketsByActionId: Record<number, number>;
  busyActionId: number | null;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  onExecute: (id: number) => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, thinking]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
      {messages.map((m) => {
        const actionId = m.content?.kind === 'action' ? m.content.actionId : null;
        return (
          <ChatMessage
            key={m.id}
            message={m}
            action={actionId !== null ? (actionsById[actionId] ?? null) : null}
            busy={actionId !== null && busyActionId === actionId}
            ticketId={actionId !== null ? (ticketsByActionId[actionId] ?? null) : null}
            onApprove={onApprove}
            onReject={onReject}
            onExecute={onExecute}
          />
        );
      })}
      {thinking && (
        <div className="flex justify-start">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            Thinking…
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
