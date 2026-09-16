import { useEffect, useState } from "react";

/**
 * Seconds remaining until `endsAtMs` (epoch ms), re-ticking every second and
 * clamped at 0. Returns 0 when `endsAtMs` is null/undefined.
 *
 * Pass `serverNowMs` (the server's clock when it sent `endsAtMs`) and the
 * countdown corrects for a device clock that disagrees with the server's -
 * without it, a phone a minute fast would show "0s / Time's Up" immediately.
 */
export function useCountdown(endsAtMs: number | null | undefined, serverNowMs?: number | null): number {
  // Tracks "server now" as best the client can tell: real client time plus the
  // client<->server offset captured when serverNowMs last changed.
  const [effectiveNowMs, setEffectiveNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (!endsAtMs) return;
    const skewMs = serverNowMs ? serverNowMs - Date.now() : 0;
    const tick = () => setEffectiveNowMs(Date.now() + skewMs);
    const initial = setTimeout(tick, 0); // re-anchor right away (async, next macrotask)
    const id = setInterval(tick, 1000);
    return () => {
      clearTimeout(initial);
      clearInterval(id);
    };
  }, [endsAtMs, serverNowMs]);

  if (!endsAtMs) return 0;
  return Math.max(0, Math.ceil((endsAtMs - effectiveNowMs) / 1000));
}
