import { apiClient } from './client';

export interface WorkspaceUser { id: number; username: string; role: 'admin' | 'agent' | 'viewer'; is_active: boolean; created_at: string }
export interface AuditEvent { id: number; actor_id: number | null; actor_username: string; event_type: string; entity_type: string; entity_id: string | null; details: Record<string, unknown> | null; created_at: string }

export async function listUsers(): Promise<WorkspaceUser[]> {
  const { data } = await apiClient.get<WorkspaceUser[]>('/api/v1/users');
  return data;
}

export async function createUser(input: { username: string; password: string; role: WorkspaceUser['role'] }): Promise<WorkspaceUser> {
  const { data } = await apiClient.post<WorkspaceUser>('/api/v1/users', input);
  return data;
}

export async function updateUser(id: number, input: { role?: WorkspaceUser['role']; is_active?: boolean; password?: string }): Promise<WorkspaceUser> {
  const { data } = await apiClient.patch<WorkspaceUser>(`/api/v1/users/${id}`, input);
  return data;
}

export async function listAuditEvents(): Promise<AuditEvent[]> {
  const { data } = await apiClient.get<AuditEvent[]>('/api/v1/audit', { params: { limit: 200 } });
  return data;
}
