/**
 * Deep-link path fixups for the custom-scheme join link.
 *
 * A scanned session QR encodes `samsungindia://join/<code>`. When the OS
 * hands that to the app, "join" is parsed as the URL authority - some
 * expo-router / RN versions keep it (`/join/<code>`), others drop it
 * (`/<code>`), and Expo Go wraps it as `exp://host/--/join/<code>`. Left
 * alone, most of those match no route ("Unmatched Route").
 *
 * This normalises every shape back to `/join/<code>` so `app/join/[code].tsx`
 * matches. A JS module expo-router loads at runtime -> ships via `eas update`
 * (a new file still needs one Metro restart with `-c` to register).
 *
 * Never throw in here - fall back to returning the path untouched.
 */
export function redirectSystemPath({ path }: { path: string; initial: boolean }): string {
  try {
    // Strip a leading scheme (samsungindia://, exp://, https://, ...).
    let p = path.replace(/^[a-z][a-z0-9+.-]*:\/\//i, "");
    // Expo Go / dev-client prefix: `host:port/--/join/CODE` -> `/join/CODE`.
    p = p.replace(/^[^/]*\/--\//, "/");
    // Collapse to a single leading slash.
    p = "/" + p.replace(/^\/+/, "");

    // Authority kept: `/join/CONF2610014`.
    const withHost = p.match(/^\/join\/([^/?#]+)/i);
    if (withHost) return `/join/${withHost[1]}`;

    // Authority dropped: a bare `/CONF2610014` is a scanned join link.
    const bareCode = p.match(/^\/(CONF\d[A-Za-z0-9]*)(?:[/?#]|$)/i);
    if (bareCode) return `/join/${bareCode[1]}`;

    return path;
  } catch {
    return path;
  }
}
