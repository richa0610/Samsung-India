import { Ionicons } from "@expo/vector-icons";

export type StatusMeta = { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string };

// Shared between ModuleDetailCard's per-module pill and the screen's overall
// status pill, so the two always agree on what each status looks like.
export const STATUS_META: Record<string, StatusMeta> = {
  Completed: { icon: "checkmark-circle-outline", color: "#059669", bg: "#ECFDF5" },
  Ongoing: { icon: "radio-outline", color: "#2563EB", bg: "#EFF6FF" },
  Scheduled: { icon: "time-outline", color: "#EA580C", bg: "#FFF7ED" },
  Missed: { icon: "close-circle-outline", color: "#DC2626", bg: "#FEF2F2" },
  Absent: { icon: "remove-circle-outline", color: "#6B7280", bg: "#F3F4F6" },
};

export const DEFAULT_STATUS_META: StatusMeta = { icon: "ellipse-outline", color: "#6B7280", bg: "#F3F4F6" };

export function statusMetaFor(status: string): StatusMeta {
  return STATUS_META[status] ?? DEFAULT_STATUS_META;
}
