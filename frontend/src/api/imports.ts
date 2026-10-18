import { apiClient } from './client';

export interface ImportResult {
  kind: 'customers' | 'tickets';
  total_rows: number;
  ready_to_import: number;
  skipped_duplicates: number;
  errors: { row: number; message: string }[];
  preview: Record<string, string | number | null>[];
  imported: number | null;
}

export async function previewCsvImport(kind: ImportResult['kind'], file: File, commit = false): Promise<ImportResult> {
  const body = new FormData();
  body.append('file', file);
  const { data } = await apiClient.post<ImportResult>(`/api/v1/imports/${kind}`, body, {
    params: { dry_run: !commit },
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
