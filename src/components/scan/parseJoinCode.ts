/**
 * Pulls the conference code out of whatever a scanned session QR encodes -
 * `samsungindia://join/CONF2610035`, `/join/CONF2610035`, or a bare
 * `CONF2610035`. Mirrors the shapes `app/+native-intent.tsx` handles.
 */
export function parseJoinCode(raw: string): string | null {
  const value = raw.trim();
  const match =
    value.match(/join\/([^/?#\s]+)/i) ?? value.match(/(CONF\d[A-Za-z0-9]*)/i);
  return match ? match[1] : null;
}
