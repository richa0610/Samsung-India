import { ModuleKey } from "./constants";
import { parseTimeToMinutes } from "./formatting";

export type FlowItemId = "attendance" | ModuleKey;

export type FlowItem = {
  id: FlowItemId;
  // "hh:mm AM/PM" or "" - Attendance uses Check-In Opens, modules use Start Time.
  startTime: string;
  // Date.now() stamp of when this item was added to the flow.
  enabledAt: number;
};

/**
 * Orders the session-flow cards: items with a start time run in ascending time
 * order; items still missing a time float to the top, newest-added first (so a
 * just-added module lands at the top and slots into place once it's timed).
 */
export function orderFlowItems(items: FlowItem[]): FlowItem[] {
  return [...items].sort((a, b) => {
    const am = a.startTime ? parseTimeToMinutes(a.startTime) : null;
    const bm = b.startTime ? parseTimeToMinutes(b.startTime) : null;
    if (am != null && bm != null) return am - bm;
    if (am != null) return 1;
    if (bm != null) return -1;
    return b.enabledAt - a.enabledAt;
  });
}
