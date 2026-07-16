const TOKEN_KEY = "docqa_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}
