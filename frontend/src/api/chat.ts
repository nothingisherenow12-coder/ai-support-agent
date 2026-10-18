import { apiClient } from './client';
import type { ActionProposal } from '../types/action';
import type { KnowledgeSource } from '../types/knowledge';

export type ChatIntent = 'knowledge' | 'data' | 'action';

// Same shape as the backend OrchestratorResponse.
export interface ChatResponse {
  intent: ChatIntent;
  answer: string;
  data: unknown | null;
  sources: KnowledgeSource[];
  requires_approval: boolean;
  action: ActionProposal | null;
  action_id: number | null;
  conversation_id: number | null;
}

export interface ChatConversation { id: number; title: string; created_at: string; updated_at: string }
export interface StoredChatMessage { id: number; role: 'user' | 'assistant'; content: string; payload: ChatResponse | null; created_at: string }

export async function sendChatMessage(message: string, context: string[] = [], conversation_id?: number): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>('/api/v1/chat', { message, context, conversation_id });
  return data;
}

export async function listConversations(): Promise<ChatConversation[]> {
  const { data } = await apiClient.get<ChatConversation[]>('/api/v1/chat/conversations');
  return data;
}

export async function getConversationMessages(id: number): Promise<StoredChatMessage[]> {
  const { data } = await apiClient.get<StoredChatMessage[]>(`/api/v1/chat/conversations/${id}/messages`);
  return data;
}

export async function deleteConversation(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/chat/conversations/${id}`);
}
