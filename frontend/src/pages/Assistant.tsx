import { useEffect, useMemo, useState } from 'react';
import { MessageSquarePlus, Trash2 } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import EmptyState from '../components/common/EmptyState';
import { deleteConversation, getConversationMessages, listConversations, sendChatMessage, type ChatConversation } from '../api/chat';
import { approveAction, executeAction, getAction, rejectAction } from '../api/actions';
import type { ActionRecord } from '../types/action';
import type { AssistantContent, ChatMessage } from '../types/chat';
import type { Customer, Ticket } from '../types/customer';
import type { KnowledgeQueryResponse } from '../types/knowledge';
import { getApiErrorMessage } from '../api/errors';

function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function now(): string {
  return new Date().toISOString();
}

function isCustomer(value: unknown): value is Customer {
  return (
    typeof value === 'object' &&
    value !== null &&
    'email' in value &&
    'name' in value
  );
}

function isTicket(value: unknown): value is Ticket {
  return typeof value === 'object' && value !== null && 'id' in value && 'title' in value && 'status' in value;
}

export default function Assistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [thinking, setThinking] = useState(false);
  const [actionRecords, setActionRecords] = useState<Record<number, ActionRecord>>({});
  const [ticketsByAction, setTicketsByAction] = useState<Record<number, number>>({});
  const [busyActionId, setBusyActionId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const actionsById = useMemo(() => actionRecords, [actionRecords]);

  async function refreshConversations() {
    try { setConversations(await listConversations()); } catch { /* Chat remains usable if history is temporarily unavailable. */ }
  }

  useEffect(() => { void refreshConversations(); }, []);

  async function openConversation(id: number) {
    setLoadingHistory(true);
    try {
      const stored = await getConversationMessages(id);
      const restored: ChatMessage[] = stored.map((row) => {
        const payload = row.payload;
        let content: AssistantContent | undefined;
        if (row.role === 'assistant' && payload?.intent === 'knowledge') {
          const response: KnowledgeQueryResponse = { answer: payload.answer, sources: payload.sources ?? [], answerable: (payload.sources ?? []).length > 0 };
          content = { kind: 'knowledge', response };
        } else if (row.role === 'assistant' && payload?.intent === 'data') {
          const data = payload.data;
          content = { kind: 'data', title: payload.answer, customer: !Array.isArray(data) && isCustomer(data) ? data : null, tickets: Array.isArray(data) ? data as Ticket[] : [], ticket: !Array.isArray(data) && isTicket(data) ? data : null };
        } else if (row.role === 'assistant' && payload?.intent === 'action' && payload.action_id !== null) {
          content = { kind: 'action', actionId: payload.action_id };
          void getAction(payload.action_id).then(storeAction).catch(() => undefined);
        } else if (row.role === 'assistant') {
          content = { kind: 'text', text: row.content };
        }
        return { id: String(row.id), role: row.role, text: row.content, content, createdAt: row.created_at };
      });
      setConversationId(id);
      setMessages(restored);
    } catch (err) {
      push('assistant', 'Could not load saved conversation.', { kind: 'error', message: getApiErrorMessage(err, 'Unable to load chat history.') });
    } finally { setLoadingHistory(false); }
  }

  function startNewConversation() {
    setConversationId(null);
    setMessages([]);
  }

  async function removeConversation() {
    if (conversationId === null || !window.confirm('Delete this conversation and its saved messages?')) return;
    try {
      await deleteConversation(conversationId);
      startNewConversation();
      await refreshConversations();
    } catch (err) {
      push('assistant', 'Could not delete saved conversation.', { kind: 'error', message: getApiErrorMessage(err, 'Unable to delete conversation.') });
    }
  }

  function push(role: ChatMessage['role'], text: string, content?: AssistantContent) {
    setMessages((prev) => [...prev, { id: uid(), role, text, content, createdAt: now() }]);
  }

  function storeAction(record: ActionRecord) {
    setActionRecords((prev) => ({ ...prev, [record.id]: record }));
  }

  async function handleSend(text: string) {
    push('user', text);
    setThinking(true);
    try {
      const context = messages.slice(-6).filter((message) => message.role === 'user').map((message) => message.text);
      const response = await sendChatMessage(text, context, conversationId ?? undefined);
      if (response.conversation_id !== null) setConversationId(response.conversation_id);
      void refreshConversations();

      if (response.intent === 'knowledge') {
        const knowledge: KnowledgeQueryResponse = {
          answer: response.answer,
          sources: response.sources,
          answerable: response.sources.length > 0,
        };
        push('assistant', response.answer, { kind: 'knowledge', response: knowledge });
        return;
      }

      if (response.intent === 'data') {
        const payload = response.data;
        const tickets = Array.isArray(payload) ? (payload as Ticket[]) : [];
        const ticket = !Array.isArray(payload) && isTicket(payload) ? payload : null;
        const customer = !Array.isArray(payload) && isCustomer(payload) ? payload : null;
        push('assistant', response.answer, {
          kind: 'data',
          title: response.answer,
          customer,
          tickets,
          ticket,
        });
        return;
      }

      if (response.intent === 'action' && response.action_id !== null) {
        let record: ActionRecord;
        try {
          record = await getAction(response.action_id);
        } catch {
          // The chat response confirms the proposal was saved. Keep a usable
          // review card even when the follow-up read briefly fails.
          const proposal = response.action;
          if (!proposal) throw new Error('The saved proposal could not be loaded.');
          record = { ...proposal, id: response.action_id, status: 'proposed', created_at: now(), updated_at: now() };
        }
        storeAction(record);
        push('assistant', response.answer, {
          kind: 'action',
          actionId: response.action_id,
        });
        return;
      }

      push('assistant', response.answer, { kind: 'text', text: response.answer });
    } catch (err) {
      push('assistant', 'Request failed.', {
        kind: 'error',
        message: getApiErrorMessage(err, 'Unable to reach the backend.'),
      });
    } finally {
      setThinking(false);
    }
  }

  async function handleApprove(id: number) {
    setBusyActionId(id);
    try {
      const approved = await approveAction(id);
      storeAction(approved);
    } catch (err) {
      push('assistant', 'Action could not be approved.', {
        kind: 'error',
        message: getApiErrorMessage(err, 'Action could not be approved.'),
      });
      try {
        storeAction(await getAction(id));
      } catch {
        // Keep the last known record if the refresh also fails.
      }
    } finally {
      setBusyActionId(null);
    }
  }

  async function handleExecute(id: number) {
    setBusyActionId(id);
    try {
      const result = await executeAction(id);
      setTicketsByAction((prev) => ({ ...prev, [id]: result.ticket.id }));
      storeAction(await getAction(id));
    } catch (err) {
      push('assistant', 'Approved action could not be executed.', { kind: 'error', message: getApiErrorMessage(err, 'Execution failed. You can retry from this card or the approval queue.') });
      try { storeAction(await getAction(id)); } catch { /* Keep the last known state. */ }
    } finally { setBusyActionId(null); }
  }

  async function handleReject(id: number) {
    setBusyActionId(id);
    try {
      storeAction(await rejectAction(id));
    } catch (err) {
      push('assistant', 'Action could not be rejected.', {
        kind: 'error',
        message: getApiErrorMessage(err, 'Action could not be rejected.'),
      });
    } finally {
      setBusyActionId(null);
    }
  }

  return (
    <PageContainer>
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-bold text-slate-900">AI Assistant</h1>
        <p className="text-sm text-slate-500">
          Unified chat: knowledge answers with sources · customer data · action proposals with
          backend-enforced approval.
        </p>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <select aria-label="Saved conversations" value={conversationId ?? ''} disabled={loadingHistory || thinking} onChange={(event) => { const id = Number(event.target.value); if (id > 0) void openConversation(id); else startNewConversation(); }} className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 sm:max-w-md"><option value="">New conversation</option>{conversations.map((conversation) => <option key={conversation.id} value={conversation.id}>{conversation.title}</option>)}</select>
        <button type="button" disabled={thinking || loadingHistory} onClick={startNewConversation} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"><MessageSquarePlus size={14}/>New chat</button>
        {conversationId !== null && <button type="button" disabled={thinking || loadingHistory} onClick={() => void removeConversation()} className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"><Trash2 size={14}/>Delete</button>}
      </div>
      {loadingHistory && <p className="mt-2 text-xs text-slate-500">Loading saved conversation…</p>}

      <div className="mt-4 flex h-[65vh] min-h-[420px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white">
        {messages.length === 0 ? (
          <div className="flex-1 overflow-y-auto bg-slate-50 p-4">
            <EmptyState
              title="Start a conversation"
              hint='Try: "What is our refund policy?" · "Show me the tickets for customer 1." · "Create a support ticket for customer 1 about a billing problem."'
            />
          </div>
        ) : (
          <ChatWindow
            messages={messages}
            thinking={thinking}
            actionsById={actionsById}
            ticketsByActionId={ticketsByAction}
            busyActionId={busyActionId}
            onApprove={handleApprove}
            onReject={handleReject}
            onExecute={handleExecute}
          />
        )}
        <ChatInput onSend={handleSend} disabled={thinking} />
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {[
          'What is our refund policy?',
          'Show me the tickets for customer 1.',
          'Create a support ticket for customer 1 about a billing problem.',
        ].map((s) => (
          <button
            key={s}
            type="button"
            disabled={thinking}
            onClick={() => handleSend(s)}
            className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-600 hover:border-slate-500 hover:text-slate-900 disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </PageContainer>
  );
}
