// Tiny in-app pub/sub for events pushed over the /ws/admin WebSocket (see
// useAuth.tsx, which owns the socket's connect/reconnect lifecycle and is
// the only thing that calls `emit`). Screens subscribe to the event types
// they care about and trigger a silent refetch, instead of each polling
// on its own interval.

export type LiveEventType = "training_created" | "trainee_created" | "attendance_marked";

export type LiveEvent = {
  type: LiveEventType;
  [key: string]: unknown;
};

type Listener = (event: LiveEvent) => void;

const listeners = new Map<LiveEventType, Set<Listener>>();

export function subscribe(type: LiveEventType, callback: Listener): () => void {
  const set = listeners.get(type) ?? new Set();
  set.add(callback);
  listeners.set(type, set);
  return () => {
    set.delete(callback);
  };
}

export function emit(event: LiveEvent): void {
  listeners.get(event.type)?.forEach((callback) => callback(event));
}
