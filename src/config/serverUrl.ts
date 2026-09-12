import { File, Paths } from "expo-file-system";

/**
 * Runtime-configurable backend URL, so a changed PC IP / Wi-Fi never needs
 * a rebuild - the trainer edits it in-app (gear on the role screen).
 *
 * Persisted as a plain string in a file (expo-file-system, already bundled).
 * Read synchronously at module load so `getApiBaseUrl()` is correct before
 * the first request; `client.ts` / `useAuth.tsx` call the getters per
 * request, so a change takes effect without an app restart.
 */

const DEFAULT_HOST = "192.168.29.95";
export const DEFAULT_API_URL =
  process.env.EXPO_PUBLIC_API_URL || `http://${DEFAULT_HOST}:8000`;

const FILE_NAME = "server-url.txt";

function storeFile(): File | null {
  try {
    return new File(Paths.document, FILE_NAME);
  } catch {
    return null;
  }
}

function normalize(input: string): string {
  const url = input.trim();
  if (!url) return DEFAULT_API_URL;
  const withScheme = /^https?:\/\//i.test(url) ? url : `http://${url}`;
  return withScheme.replace(/\/+$/, "");
}

let currentUrl = DEFAULT_API_URL;
try {
  const f = storeFile();
  if (f?.exists) {
    const v = f.textSync().trim();
    if (v) currentUrl = v;
  }
} catch {
  // keep the default
}

export function getApiBaseUrl(): string {
  return currentUrl;
}

export function getWsBaseUrl(): string {
  return currentUrl.replace(/^http/i, "ws");
}

export function getStoredServerUrl(): string {
  return currentUrl;
}

export function isUsingDefaultServerUrl(): boolean {
  return currentUrl === DEFAULT_API_URL;
}

export function setServerUrl(input: string): string {
  currentUrl = normalize(input);
  try {
    const f = storeFile();
    if (f) {
      if (!f.exists) f.create();
      f.write(currentUrl);
    }
  } catch {
    // in-memory value still applies for this session
  }
  return currentUrl;
}

export function resetServerUrl(): string {
  currentUrl = DEFAULT_API_URL;
  try {
    const f = storeFile();
    if (f?.exists) f.delete();
  } catch {
    // ignore
  }
  return currentUrl;
}
