import { persistedText } from "./persistedText";

/**
 * Runtime-configurable backend URL, so a changed PC IP / Wi-Fi never needs
 * a rebuild - the trainer edits it in-app (gear on the role screen).
 *
 * Persisted as a plain string in a file (see persistedText). Read
 * synchronously at module load so `getApiBaseUrl()` is correct before
 * the first request; `client.ts` / `useAuth.tsx` call the getters per
 * request, so a change takes effect without an app restart.
 */

const DEFAULT_HOST = "129.121.73.181";
export const DEFAULT_API_URL = process.env.EXPO_PUBLIC_API_URL
  ? normalize(process.env.EXPO_PUBLIC_API_URL)
  : `http://${DEFAULT_HOST}:8000`;

const store = persistedText("server-url.txt");

function normalize(input: string): string {
  const url = input.trim();
  if (!url) return DEFAULT_API_URL;
  const withScheme = /^https?:\/\//i.test(url) ? url : `http://${url}`;
  return withScheme.replace(/\/+$/, "");
}

const storedUrl = store.read();
let currentUrl = storedUrl ? normalize(storedUrl) : DEFAULT_API_URL;

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
  store.write(currentUrl);
  return currentUrl;
}

export function resetServerUrl(): string {
  currentUrl = DEFAULT_API_URL;
  store.remove();
  return currentUrl;
}
