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
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  const requestId = res.headers.get("x-request-id") || undefined;

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new APIError(
      `HTTP ${res.status}: ${text}`,
      res.status,
      requestId
    );
  }

  const body: APIResponse<T> = await res.json();
  body.request_id = body.request_id || requestId;
  return body;
}

export const api = {
  health: () => request<HealthData>("/api/health"),
  ready: () => request<ReadinessData>("/api/health/ready"),
};

export { APIError };
