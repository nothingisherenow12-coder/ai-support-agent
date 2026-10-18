import { apiClient } from './client';
import type { ActionProposal, ActionRecord, ExecuteActionResult } from '../types/action';

export async function listActions(status?: string): Promise<ActionRecord[]> {
  const { data } = await apiClient.get<ActionRecord[]>('/api/v1/actions', {
    params: status ? { status } : {},
  });
  return data;
}

export async function getAction(actionId: number): Promise<ActionRecord> {
  const { data } = await apiClient.get<ActionRecord>(`/api/v1/actions/${actionId}`);
  return data;
}

export async function proposeAction(proposal: ActionProposal): Promise<ActionRecord> {
  const { data } = await apiClient.post<ActionRecord>('/api/v1/actions', proposal);
  return data;
}

export async function approveAction(actionId: number): Promise<ActionRecord> {
  const { data } = await apiClient.post<ActionRecord>(`/api/v1/actions/${actionId}/approve`);
  return data;
}

export async function rejectAction(actionId: number): Promise<ActionRecord> {
  const { data } = await apiClient.post<ActionRecord>(`/api/v1/actions/${actionId}/reject`);
  return data;
}

export async function executeAction(actionId: number): Promise<ExecuteActionResult> {
  const { data } = await apiClient.post<ExecuteActionResult>(
    `/api/v1/actions/${actionId}/execute`,
  );
  return data;
}
