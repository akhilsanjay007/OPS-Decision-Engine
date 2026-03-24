const DEFAULT_API_BASE_URL = "http://localhost:8000";

/**
 * Resolves the FastAPI base URL.
 * Prefer setting `NEXT_PUBLIC_API_URL`; when unset, defaults to localhost for local dev.
 */
export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!raw) {
    return DEFAULT_API_BASE_URL;
  }
  return raw.replace(/\/+$/, "");
}
