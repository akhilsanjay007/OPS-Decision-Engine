const DEFAULT_API_BASE_URL = "http://localhost:8000";

/**
 * Resolves the FastAPI base URL from `NEXT_PUBLIC_API_BASE_URL`.
 * When unset, defaults to localhost for local dev and Docker browser access.
 */
export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (!raw) {
    return DEFAULT_API_BASE_URL;
  }
  return raw.replace(/\/+$/, "");
}
