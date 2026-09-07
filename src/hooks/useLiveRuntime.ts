import { useEffect, useState } from "react";

/**
 * Live session runtime in seconds, derived from the real timestamps on the
 * session dashboard response (`SessionDashboard.actualStartedAt` /
 * `actualEndedAt`, ISO strings):
 *
 *  - not started (no `startedAt`)  -> 0
 *  - ended (`endedAt` set)         -> endedAt - startedAt, frozen
 *  - running                       -> now - startedAt, re-ticking every second
 *
 * The backend tags every timestamp it sends here with an explicit UTC
 * offset (`date_utils.to_utc_iso`), so `Date.parse` below always converts
 * correctly to the device's own local time - regardless of what timezone
 * the backend server itself runs in. Was previously a same-timezone
 * assumption (bare, offset-less timestamps) that broke the moment the
 * backend moved off a same-venue machine onto a cloud host in a different
 * timezone - every "live" duration on this screen was off by exactly the
 * device's UTC offset (5h30m for IST) until that got fixed server-side.
 */
export function useLiveRuntime(
  startedAt: string | null | undefined,
  endedAt: string | null | undefined,
): number {
  const startMs = startedAt ? Date.parse(startedAt) : NaN;
  const endMs = endedAt ? Date.parse(endedAt) : NaN;
  const running = !Number.isNaN(startMs) && Number.isNaN(endMs);

  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(id);
  }, [running]);

  if (Number.isNaN(startMs)) return 0;
  const until = Number.isNaN(endMs) ? nowMs : endMs;
  return Math.max(0, Math.floor((until - startMs) / 1000));
}
