import { getCompany } from "@/config/company";
import { getApiBaseUrl } from "@/constants/api";

/** The company this device signs in to, on every request - the server reads it only before
 *  sign-in (afterwards the token's own tenant wins), so sending it always is harmless. */
function companyHeader(): Record<string, string> {
  const company = getCompany();
  return company ? { "X-Tenant-ID": company.tenantId } : {};
}

export class ApiError extends Error {
  status: number;
  /** The parsed `detail` from the error response - a string, or an object
   *  like `{ code, message, ... }` for structured errors the UI branches on. */
  body: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function errorFromResponse(status: number, data: unknown): ApiError {
  const detail = (data as { detail?: unknown } | null)?.detail;
  const message =
    typeof detail === "string"
      ? detail
      : typeof (detail as { message?: unknown })?.message === "string"
        ? (detail as { message: string }).message
        : "Something went wrong. Please try again.";
  return new ApiError(message, status, detail);
}

/** Told the token of a signed-in request the server answered 401 - the one answer it gives a
 *  request carrying a token that's no longer good (expired, signed out, or signed out by a sign-in
 *  on another device - `code` "SIGNED_IN_ELSEWHERE"); a wrong password at login is a 401 too, but a
 *  login carries no token. AuthProvider registers this, and signs that sign-in out once, wherever in
 *  the app the request was made. */
type SessionEndedHandler = (token: string, code?: string) => void;
let onSessionEnded: SessionEndedHandler | null = null;

export function setSessionEndedHandler(handler: SessionEndedHandler | null) {
  onSessionEnded = handler;
}

function codeOf(body: unknown): string | undefined {
  const code = (body as { code?: unknown } | null)?.code;
  return typeof code === "string" ? code : undefined;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  // A sign-in names no company (user, 2026-10-19): the server finds it - an old one saved on this
  // phone must not steer it elsewhere.
  { company = true }: { company?: boolean } = {},
): Promise<T> {
  let response: Response;
  const base = getApiBaseUrl();
  const headers = {
    "Content-Type": "application/json",
    ...(company ? companyHeader() : {}),
    ...options.headers,
  } as Record<string, string>;

  try {
    response = await fetch(`${base}${path}`, { ...options, headers });
  } catch (err) {
    console.warn(`[apiRequest] ${base}${path} failed:`, err instanceof Error ? err.message : err);
    throw new ApiError(
      "Couldn't reach the server. Check your connection and try again.",
      0
    );
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const token = headers.Authorization?.startsWith("Bearer ") ? headers.Authorization.slice("Bearer ".length) : null;
    const error = errorFromResponse(response.status, data);
    if (response.status === 401 && token) onSessionEnded?.(token, codeOf(error.body));
    throw error;
  }

  return data as T;
}

// Separate from apiRequest because it must NOT set Content-Type: fetch
// needs to generate its own multipart boundary for FormData bodies.
export async function apiUpload<T>(
  path: string,
  formData: FormData,
  token: string,
  timeoutMs = 25000
): Promise<T> {
  let response: Response;
  const base = getApiBaseUrl();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    response = await fetch(`${base}${path}`, {
      method: "POST",
      headers: { ...companyHeader(), Authorization: `Bearer ${token}` },
      body: formData,
      signal: controller.signal,
    });
  } catch (err) {
    const detail = err instanceof Error ? `${err.name}: ${err.message}` : String(err);
    console.warn(`[apiUpload] ${base}${path} failed:`, detail);
    // Weak venue Wi-Fi can stall a multipart upload long enough to trip the
    // AbortController above - give that case a message that points at the
    // connection quality rather than the generic "can't reach server" one.
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError(
        "Upload timed out - your connection may be too weak. Please try again.",
        0
      );
    }
    throw new ApiError(
      "Couldn't reach the server. Check your connection and try again.",
      0
    );
  } finally {
    clearTimeout(timer);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const error = errorFromResponse(response.status, data);
    if (response.status === 401) onSessionEnded?.(token, codeOf(error.body));
    throw error;
  }

  return data as T;
}
