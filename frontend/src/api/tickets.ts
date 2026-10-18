import { apiClient } from './client';
import type { Ticket } from '../types/customer';
import type { Page } from './customers';

export interface TicketFilters {
  status?: string;
  priority?: string;
  customer_id?: number;
  q?: string;
  limit?: number;
  offset?: number;
}

export async function listTickets(filters: TicketFilters = {}): Promise<Page<Ticket>> {
  const { data } = await apiClient.get<Page<Ticket>>('/api/v1/tickets', { params: filters });
  return data;
}

export async function updateTicket(ticketId: number, update: { status?: string; priority?: string }): Promise<Ticket> {
  const { data } = await apiClient.patch<Ticket>(`/api/v1/tickets/${ticketId}`, update);
  return data;
}
