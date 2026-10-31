/**
 * Reads what the server writes into a sign-in token (a JWT: header.payload.signature, the payload
 * base64url JSON) - its expiry (`exp`, in seconds) and, for staff, which kind of account it is.
 * Nothing is verified here - the server does that on every request; this only spares restoring a
 * sign-in that has plainly run out, and picks the area a staff account's requests go to.
 */

function tokenClaims(token: string): Record<string, unknown> | null {
  const payload = token.split(".")[1];
  if (!payload) return null;
  try {
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(payload.length / 4) * 4, "=");
    const claims: unknown = JSON.parse(atob(base64));
    return claims && typeof claims === "object" ? (claims as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function expiresAtMs(token: string): number | null {
  const exp = tokenClaims(token)?.exp;
  return typeof exp === "number" ? exp * 1000 : null;
}

/** True once the token's expiry has passed. A token this can't read counts as not expired - the
 *  server is the judge, and its 401 signs the user out (see setSessionEndedHandler in api/client). */
export function isTokenExpired(token: string, nowMs: number = Date.now()): boolean {
  const expiry = expiresAtMs(token);
  return expiry !== null && expiry <= nowMs;
}

export type StaffArea = "trainer" | "admin";

/** The staff area a staff token's requests go to (user, 2026-10-31): a trainer's - by its `role`
 *  claim, or for a token without one its `agencyteam:` subject - is /trainer; any other is /admin.
 *  The server refuses each kind in the other's area. */
export function staffArea(token: string): StaffArea {
  const claims = tokenClaims(token);
  const subject = typeof claims?.sub === "string" ? claims.sub : "";
  return claims?.role === "trainer" || (claims?.role === undefined && subject.startsWith("agencyteam:")) ? "trainer" : "admin";
}
