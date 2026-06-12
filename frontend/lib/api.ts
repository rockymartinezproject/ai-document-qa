/**
 * Typed API client for the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string | null;
  request_id?: string | null;
}

export interface HealthData {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  uptime_seconds: number;
  dependencies?: Record<string, boolean> | null;
}

export interface ReadinessData {
  status: string;
  checks: Record<string, boolean>;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
  message: string;
}

export interface URLIngestResponse {
  id: string;
  filename: string;
  url: string;
  title: string;
  text_length: number;
  status: string;
  created_at: string;
  message: string;
}

export interface DocumentOut {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface SearchResult {
  id: string;
  score: number;
  document_id: string;
  text: string;
  source: string;
  index: number;
  start_char: number;
  end_char: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}

export interface VectorStoreStatus {
  collection_name: string;
  qdrant_host: string;
  qdrant_port: number;
  total_points: number;
  is_healthy: boolean;
}

export interface SyncDocumentResponse {
  document_id: string;
  points_synced: number;
  message: string;
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public requestId?: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<APIResponse<T>> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      ...options?.headers,
    },
    ...options,
  });

  const requestId = res.headers.get("x-request-id") || undefined;

  if (!res.ok) {
    let detail = "Unknown error";
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await res.text().catch(() => "Unknown error");
    }
    throw new APIError(`HTTP ${res.status}: ${detail}`, res.status, requestId);
  }

  const body: APIResponse<T> = await res.json();
  body.request_id = body.request_id || requestId;
  return body;
}

export const api = {
  health: () => request<HealthData>("/api/health"),
  ready: () => request<ReadinessData>("/api/health/ready"),

  documents: {
    list: () => request<DocumentOut[]>("/api/documents"),
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<DocumentUploadResponse>("/api/documents/upload", {
        method: "POST",
        body: form,
      });
    },
    uploadUrl: (url: string) => {
      return request<URLIngestResponse>("/api/documents/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
    },
  },

  search: {
    status: () => request<VectorStoreStatus>("/api/search/status"),
    query: (query: string, top_k = 5, document_id?: string) => {
      return request<SearchResponse>("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k, document_id }),
      });
    },
    syncDocument: (documentId: string) => {
      return request<SyncDocumentResponse>(`/api/search/sync/${documentId}`, {
        method: "POST",
      });
    },
  },
};

export { APIError };
