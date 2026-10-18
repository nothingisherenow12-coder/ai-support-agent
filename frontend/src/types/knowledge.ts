export interface KnowledgeSource {
  document_id: number;
  filename: string;
  chunk_id: number;
  chunk_index: number;
  distance: number;
}

export interface KnowledgeQueryRequest {
  question: string;
  top_k?: number;
}

export interface KnowledgeQueryResponse {
  answer: string;
  sources: KnowledgeSource[];
  answerable: boolean;
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  chunks_created: number;
}

export interface UploadedDocument {
  id: number;
  filename: string;
  chunks_created: number;
  created_at: string;
}
