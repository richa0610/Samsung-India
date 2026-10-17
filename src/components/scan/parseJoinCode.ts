/**
 * Pulls the conference code out of whatever a scanned session QR encodes -
 * `samsungindia://join/<code>`, `/join/<code>`, or a bare code - where a code is the training ID
 * followed by its signature (`CONF2698735081.K3J9XQ2M7PLA4TZB`), or the bare ID an older QR carries.
 * Mirrors the shapes `app/+native-intent.tsx` handles.
 */
export function parseJoinCode(raw: string): string | null {
  const value = raw.trim();
  const match =
    value.match(/join\/([^/?#\s]+)/i) ?? value.match(/(CONF\d[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?)/i);
  return match ? match[1] : null;
}
