import { LogBox } from "react-native";

/**
 * "java.lang.RuntimeException: Timeouted: JPromise was destroyed!"
 *
 * A native (Expo / Nitro) call was still in flight when the JS runtime was torn
 * down - a Metro reload, Fast Refresh, or the app being killed mid-call - so its
 * promise rejects into a runtime that no longer has a handler for it. It is
 * harmless (nothing is waiting on that result any more) and can't be caught at
 * the call site because the call was made by native/library code, so it is
 * filtered globally here instead. Every other unhandled rejection is still
 * reported exactly as before.
 */
const DESTROYED_PROMISE = /JPromise was destroyed/i;

const isDestroyedPromise = (error: unknown): boolean =>
  DESTROYED_PROMISE.test(
    error instanceof Error ? error.message : typeof error === "string" ? error : String((error as { message?: unknown })?.message ?? ""),
  );

// Hides the red LogBox overlay for this message (the log line is still printed).
LogBox.ignoreLogs([DESTROYED_PROMISE]);

// Best effort: stop Hermes reporting it as an "Uncaught (in promise)" at all,
// while still logging any other unhandled rejection the way React Native does.
const hermes = (globalThis as { HermesInternal?: { enablePromiseRejectionTracker?: (options: object) => void } })
  .HermesInternal;
try {
  hermes?.enablePromiseRejectionTracker?.({
    allRejections: true,
    onUnhandled: (id: number, error: unknown) => {
      if (isDestroyedPromise(error)) return;
      console.error(`Uncaught (in promise, id: ${id})`, error);
    },
    onHandled: () => {},
  });
} catch {
  // Tracker not available on this engine - the LogBox filter above still applies.
}
