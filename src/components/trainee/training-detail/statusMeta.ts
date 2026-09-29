import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/theme/colors";

export type StatusMeta = { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string };

// Shared between ModuleDetailCard's per-module pill and the screen's overall
// status pill, so the two always agree on what each status looks like.
export const STATUS_META: Record<string, StatusMeta> = {
  Completed: { icon: "checkmark-circle-outline", color: "#059669", bg: Colors.successBgSoft },
  Ongoing: { icon: "radio-outline", color: Colors.blueAccent, bg: Colors.blue50 },
  Scheduled: { icon: "time-outline", color: "#EA580C", bg: "#FFF7ED" },
  Missed: { icon: "close-circle-outline", color: Colors.danger, bg: Colors.dangerBgSoft },
  Absent: { icon: "remove-circle-outline", color: Colors.gray500, bg: Colors.gray100 },
};

export const DEFAULT_STATUS_META: StatusMeta = { icon: "ellipse-outline", color: Colors.gray500, bg: Colors.gray100 };

export function statusMetaFor(status: string): StatusMeta {
  return STATUS_META[status] ?? DEFAULT_STATUS_META;
}
