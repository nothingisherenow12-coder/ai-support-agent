import { apiClient } from './client';
import type { Customer, Ticket } from '../types/customer';

export interface Page<T> { items: T[]; total: number; limit: number; offset: number }

export interface NewCustomer {
  name: string;
  email: string;
  company?: string | null;
}

export async function createCustomer(customer: NewCustomer): Promise<Customer> {
  const { data } = await apiClient.post<Customer>('/api/v1/customers', customer);
  return data;
}

export async function listCustomers(query = '', limit = 25, offset = 0): Promise<Page<Customer>> {
  const { data } = await apiClient.get<Page<Customer>>('/api/v1/customers', {
    params: { limit, offset, ...(query.trim() ? { q: query.trim() } : {}) },
  });
  return data;
}

export async function getCustomer(customerId: number): Promise<Customer> {
  const { data } = await apiClient.get<Customer>(`/api/v1/customers/${customerId}`);
  return data;
}

export async function getCustomerTickets(customerId: number, limit = 25, offset = 0): Promise<Page<Ticket>> {
  const { data } = await apiClient.get<Page<Ticket>>(`/api/v1/customers/${customerId}/tickets`, { params: { limit, offset } });
  return data;
}
