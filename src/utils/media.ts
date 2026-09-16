import { getApiBaseUrl } from "@/constants/api";

export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (
    path.startsWith("http://") ||
    path.startsWith("https://") ||
    path.startsWith("file://") ||
    path.startsWith("data:")
  ) {
    return path;
  }
  // Resolved per call so a changed server URL (gear on the role screen) takes
  // effect without an app restart.
  const cleanBase = getApiBaseUrl().replace(/\/api\/?$/, "").replace(/\/+$/, "");
  // Stored paths are relative to the media root (e.g. "trainer_photos/x.jpg"),
  // but the backend only serves them under the /media prefix (see
  // backend/app/routers/media.py) - without it this 404s instead of hitting
  // the real route.
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${cleanBase}/media${cleanPath}`;
}
