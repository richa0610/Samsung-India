/**
 * Reads the expiry the server writes into a sign-in token (a JWT: header.payload.signature, the
 * payload base64url JSON with `exp` in seconds). Nothing is verified here - the server does that on
 * every request; this only spares restoring a sign-in that has plainly run out.
 */

function expiresAtMs(token: string): number | null {
  const payload = token.split(".")[1];
  if (!payload) return null;
  try {
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(payload.length / 4) * 4, "=");
    const exp = JSON.parse(atob(base64))?.exp;
    return typeof exp === "number" ? exp * 1000 : null;
  } catch {
    return null;
  }
}

/** True once the token's expiry has passed. A token this can't read counts as not expired - the
 *  server is the judge, and its 401 signs the user out (see setSessionEndedHandler in api/client). */
export function isTokenExpired(token: string, nowMs: number = Date.now()): boolean {
  const expiry = expiresAtMs(token);
  return expiry !== null && expiry <= nowMs;
}
