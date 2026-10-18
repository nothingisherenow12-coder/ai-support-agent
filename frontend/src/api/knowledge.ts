import { apiClient } from './client';
import type { DocumentUploadResponse, KnowledgeQueryResponse } from '../types/knowledge';

export async function queryKnowledge(question: string, top_k = 5): Promise<KnowledgeQueryResponse> {
  const { data } = await apiClient.post<KnowledgeQueryResponse>('/api/v1/knowledge/query', {
    question,
    top_k,
  });
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await apiClient.post<DocumentUploadResponse>('/api/v1/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const { data } = await apiClient.get('/api/v1/health');
  return data as { status: string; service: string };
}

export async function listDocuments(): Promise<Array<{ id: number; filename: string; created_at: string; chunks_created: number }>> {
  const { data } = await apiClient.get('/api/v1/documents');
  return data;
}

export async function deleteDocument(documentId: number): Promise<void> {
  await apiClient.delete(`/api/v1/documents/${documentId}`);
}
