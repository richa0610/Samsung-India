import { useEffect, useRef, useState } from "react";

import { getWsBaseUrl } from "@/constants/api";

// Subscribes to a conference's `/ws/live` room. The server only ever pushes
// thin nudges (`{ "type": "session" | "live_quiz" | "attendance" }`) - any of
// them just means "something changed, refetch". `onSignal` should refetch
// whatever REST view the screen shows. Auto-reconnects on drop, same as the
// /ws/admin socket in useAuth.tsx. Returns `connected` so callers can slow
// their fallback polling while the socket is up.
const RECONNECT_DELAY_MS = 3000;

export function useLiveQuizChannel(
  conferenceUid: string | null | undefined,
  token: string | null | undefined,
  onSignal: () => void,
): { connected: boolean } {
  const onSignalRef = useRef(onSignal);
  useEffect(() => {
    onSignalRef.current = onSignal;
  });

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!conferenceUid || !token) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const connect = () => {
      socket = new WebSocket(`${getWsBaseUrl()}/ws/live/${conferenceUid}?token=${token}`);
      socket.onopen = () => {
        if (!stopped) setConnected(true);
      };
      socket.onmessage = (event) => {
        try {
          // Any well-formed message is a "refetch" nudge - the real state
          // travels over REST, so the payload's `type` doesn't matter here.
          JSON.parse(event.data as string);
          onSignalRef.current();
        } catch {
          // ignore malformed pushes
        }
      };
      socket.onclose = () => {
        if (!stopped) {
          setConnected(false);
          reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };
      socket.onerror = () => socket?.close();
    };
    connect();

    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [conferenceUid, token]);

  return { connected };
}
