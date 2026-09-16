import { getApiBaseUrl } from "@/constants/api";

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

// Only called when USE_MOCK_DATA is false (see src/config/dataSource.ts).
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let response: Response;
  const base = getApiBaseUrl();

  try {
    response = await fetch(`${base}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch (err) {
    console.warn(`[apiRequest] ${base}${path} failed:`, err instanceof Error ? err.message : err);
    throw new ApiError(
      "Couldn't reach the server. Check your connection and try again.",
      0
    );
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw errorFromResponse(response.status, data);
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
      headers: { Authorization: `Bearer ${token}` },
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
    throw errorFromResponse(response.status, data);
  }

  return data as T;
}
