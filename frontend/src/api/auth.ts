import { apiClient } from './client';

export interface WorkspaceSession { username: string; role: 'admin' | 'agent' | 'viewer' }

export async function signIn(username: string, password: string): Promise<void> {
  await apiClient.post('/api/v1/auth/login', { username, password });
}

export async function checkSession(): Promise<WorkspaceSession | null> {
  try { const { data } = await apiClient.get<WorkspaceSession>('/api/v1/auth/session'); return data; }
  catch { return null; }
}

export async function signOut(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout');
}

export async function changePassword(current_password: string, new_password: string): Promise<void> {
  await apiClient.post('/api/v1/auth/password', { current_password, new_password });
}
