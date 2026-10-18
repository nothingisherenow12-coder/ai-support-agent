import type { Customer, Ticket } from './customer';

import type { KnowledgeQueryResponse } from './knowledge';

export type ChatRole = 'user' | 'assistant';

export interface KnowledgeContent {
  kind: 'knowledge';
  response: KnowledgeQueryResponse;
}

export interface DataContent {
  kind: 'data';
  title: string;
  customer?: Customer | null;
  tickets?: Ticket[];
  ticket?: Ticket | null;
}

export interface ActionContent {
  kind: 'action';
  actionId: number;
}

export interface TextContent {
  kind: 'text';
  text: string;
}

export interface ErrorContent {
  kind: 'error';
  message: string;
}

export type AssistantContent =
  | KnowledgeContent
  | DataContent
  | ActionContent
  | TextContent
  | ErrorContent;

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  content?: AssistantContent;
  createdAt: string;
}
