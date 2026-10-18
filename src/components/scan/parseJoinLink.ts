/** What a scanned session QR / shared join link carries. */
export type JoinLink = {
  /** The training ID followed by its signature (`CONF2698735081.K3J9XQ2M7PLA4TZB`), or the bare ID
   *  an older QR carries. */
  code: string;
  /** The company (tenant ID) the training belongs to - absent on QR codes made before
   *  2026-10-18. Only a hint for switching company; the server checks the code itself. */
  company: string | null;
};

const CODE = /join\/([^/?#\s]+)/i;
const BARE_CODE = /(CONF\d[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?)/i;
const COMPANY = /[?&]company=([^&#\s]+)/i;

function decoded(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return decodeURIComponent(value).trim() || null;
  } catch {
    return null;
  }
}

/**
 * Pulls the join code - and the company, when the link names one - out of whatever a scanned
 * session QR encodes: `samsungindia://join/<code>?company=<tenantId>`, `/join/<code>`, or a bare
 * code. Mirrors the shapes `app/+native-intent.tsx` handles.
 */
export function parseJoinLink(raw: string): JoinLink | null {
  const value = raw.trim();
  const code = (value.match(CODE) ?? value.match(BARE_CODE))?.[1];
  return code ? { code, company: decoded(value.match(COMPANY)?.[1]) } : null;
}
