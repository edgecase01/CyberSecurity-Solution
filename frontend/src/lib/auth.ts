const TOKEN_KEY = "cybersec_access_token";
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getLoginUrl(): string {
  return `${API_BASE}/auth/login`;
}

export function authHeaders(): HeadersInit {
  const token = getAccessToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export async function enqueueEmailScan(): Promise<{ task_id: string; status: string }> {
  const response = await fetch(`${API_BASE}/tasks/scan-email`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(`Email scan failed (${response.status})`);
  }
  return response.json();
}

export function captureTokenFromUrl(): boolean {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) return false;

  setAccessToken(token);
  params.delete("token");
  const path = window.location.pathname;
  const query = params.toString();
  window.history.replaceState({}, "", query ? `${path}?${query}` : path);
  return true;
}
