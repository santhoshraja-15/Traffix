import { API_BASE_URL, API_TIMEOUT_MS, API_MAX_RETRIES } from "../lib/constants";

// ── Error class ──────────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public endpoint?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Timeout wrapper ───────────────────────────────────────────────────────────
// Exported so callers hitting a URL outside the /api prefix (e.g. the root
// -level /health probe — see networkApi.ts::fetchHealth) can still get a
// bounded wait instead of a raw, un-timeout-protected fetch(). A hung
// backend (port occupied by an unrelated process, network partition, etc.)
// must fail into the app's real "data unavailable" state within a bounded
// time, never spin a "Loading…" label forever.
export function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = API_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal }).finally(() =>
    clearTimeout(timer)
  );
}

// ── Core request with retry ──────────────────────────────────────────────────
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retries: number = API_MAX_RETRIES
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  let lastError: Error = new Error("Unknown error");

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(
        url,
        { ...options, headers },
        API_TIMEOUT_MS
      );

      if (!response.ok) {
        throw new ApiError(
          response.status,
          `HTTP ${response.status}: ${response.statusText}`,
          endpoint
        );
      }

      return (await response.json()) as T;
    } catch (err) {
      lastError = err as Error;
      // Don't retry on 4xx client errors
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) {
        break;
      }
      // Backoff before retry
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 300 * (attempt + 1)));
      }
    }
  }

  throw lastError;
}

// ── Typed GET / POST helpers ─────────────────────────────────────────────────
export const apiGet = <T>(endpoint: string) =>
  apiRequest<T>(endpoint, { method: "GET" });

export const apiPost = <T>(endpoint: string, body: unknown) =>
  apiRequest<T>(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const apiPut = <T>(endpoint: string, body: unknown) =>
  apiRequest<T>(endpoint, {
    method: "PUT",
    body: JSON.stringify(body),
  });

export const apiDelete = <T>(endpoint: string) =>
  apiRequest<T>(endpoint, { method: "DELETE" });
