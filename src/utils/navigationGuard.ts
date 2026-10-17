// Firing a second router.replace()/push() while the previous one's screen
// transition hasn't finished mounting can crash Fabric (New Architecture)
// with "IllegalStateException: The specified child already has a parent" -
// it tries to attach a view that's still being inserted for the outgoing
// screen. This is a real, reproducible crash (not a guess), hit via rapid
// taps between the trainee bottom-nav tabs (Home/Dashboard/Rank/Profile),
// which all replace() each other.
//
// Module-level (not React state) is deliberate: it needs to block a second
// navigation fired from a DIFFERENT screen's freshly-mounted handler within
// the cooldown window, which a per-component ref can't do since each screen
// is a fresh mount.
let lastNavigationAt = 0;
const NAVIGATION_COOLDOWN_MS = 400;

/** Call before every replace()/push() driven by a tap (tab icons, back
 * handlers). Returns false - and the caller should skip navigating - if a
 * navigation is already settling. */
export function canNavigate(): boolean {
  const now = Date.now();
  if (now - lastNavigationAt < NAVIGATION_COOLDOWN_MS) return false;
  lastNavigationAt = now;
  return true;
}
