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

export interface DocumentActionResponse {
  id: string;
  action: string;
  success: boolean;
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

export interface Citation {
  chunk_id: string;
  document_id: string;
  source: string;
  index: number;
  text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  provider: string;
  query: string;
  conversation_id: string;
}

export type ChatStreamEvent =
  | { type: "citations"; citations: Citation[]; request_id?: string }
  | { type: "token"; token: string; request_id?: string }
  | {
      type: "done";
      answer: string;
      citations: Citation[];
      provider: string;
      request_id?: string;
    }
  | { type: "error"; message: string; request_id?: string };

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  provider?: string;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
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

export async function* askStream(
  query: string,
  conversation_id?: string,
  document_id?: string,
  search_type: "semantic" | "keyword" | "hybrid" = "hybrid",
  rerank = true,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent> {
  const url = `${API_BASE}/api/chat/stream`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, conversation_id, document_id, search_type, rerank }),
    signal,
  });

  if (!res.ok) {
    let detail = "Unknown error";
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await res.text().catch(() => "Unknown error");
    }
    throw new APIError(`HTTP ${res.status}: ${detail}`, res.status);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new APIError("No response body", 0);
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6).trim();
        if (data === "[DONE]") return;
        if (data) {
          yield JSON.parse(data) as ChatStreamEvent;
        }
      }
    }
  }
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
    delete: (id: string) =>
      request<DocumentActionResponse>(`/api/documents/${id}`, {
        method: "DELETE",
      }),
    reindex: (id: string) =>
      request<DocumentActionResponse>(`/api/documents/${id}/reindex`, {
        method: "POST",
      }),
  },

  search: {
    status: () => request<VectorStoreStatus>("/api/search/status"),
    query: (
      query: string,
      top_k = 5,
      document_id?: string,
      search_type: "semantic" | "keyword" | "hybrid" = "hybrid",
      rerank = true
    ) => {
      return request<SearchResponse>("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k, document_id, search_type, rerank }),
      });
    },
    syncDocument: (documentId: string) => {
      return request<SyncDocumentResponse>(`/api/search/sync/${documentId}`, {
        method: "POST",
      });
    },
  },

  chat: {
    ask: (
      query: string,
      conversation_id?: string,
      document_id?: string,
      search_type: "semantic" | "keyword" | "hybrid" = "hybrid",
      rerank = true
    ) => {
      return request<ChatResponse>("/api/chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, conversation_id, document_id, search_type, rerank }),
      });
    },
  },

  conversations: {
    list: () => request<Conversation[]>("/api/conversations"),
    create: (title?: string) => {
      return request<Conversation>("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
    },
    get: (id: string, limit = 100, offset = 0) =>
      request<ConversationDetail>(`/api/conversations/${id}?limit=${limit}&offset=${offset}`),
    update: (id: string, title: string) => {
      return request<Conversation>(`/api/conversations/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
    },
    delete: (id: string) =>
      request<{ deleted: boolean }>(`/api/conversations/${id}`, {
        method: "DELETE",
      }),
  },
};

export { APIError };
