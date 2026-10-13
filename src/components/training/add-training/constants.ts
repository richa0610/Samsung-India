import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { SelectOption } from "@/components/ui/SearchableSelect";
import { findZone } from "@/utils/zones";

export const ICON_BADGE_BG = "#E3ECFF";

// Built-in zones and regions for the admin filter bar and the New Trainee form only - the Add
// Training form reads them from the master list (/admin/zones). Keyed by the master's zone names;
// look a zone up with regionsForZone, not by indexing: "North Zone" is the same zone as "North".
export const REGIONS_BY_ZONE: Record<string, string[]> = {
  North: ["North 1", "North 2", "North 3", "North 4"],
  South: ["South 1", "South 2", "South 3", "South 4", "South 1 [KR]", "South 1 [TN]"],
  East: ["East 1", "East 2", "East 3", "East 4"],
  West: ["West 1", "West 2", "West 3", "West 4"],
};
export const ZONES = Object.keys(REGIONS_BY_ZONE);

/** The regions of a zone, whichever way it is spelled ("North" or "North Zone"). */
export function regionsForZone(zone: string | null | undefined): string[] {
  const name = findZone(ZONES, zone);
  return name ? REGIONS_BY_ZONE[name] : [];
}

export const COMPANY_OPTIONS: SelectOption[] = [{ label: "Samsung India", value: "Samsung India" }];

export const REQUESTED_BY_OPTIONS: SelectOption[] = [
  { label: "Quess Corp Ltd", value: "Quess Corp Ltd" },
  { label: "Other", value: "Other" },
];

// Training Hub / Audience / Session Type / Training Type pickers have no
// static option list - they're populated from the /admin catalog endpoints
// (distinct values this tenant has used on past trainings).

export const UNLOCK_CONDITIONS = ["Automatic", "Manual Broadcast"];

export type ModuleKey = "standardTest" | "liveQuiz" | "survey";
export const MODULE_LABELS: Record<ModuleKey, string> = {
  standardTest: "Standard Test",
  liveQuiz: "Live Quiz (FFF)",
  survey: "Survey",
};
export const MODULE_ICONS: Record<ModuleKey, keyof typeof Ionicons.glyphMap> = {
  standardTest: "document-text",
  liveQuiz: "flash",
  survey: "happy",
};
export const ATTENDANCE_ICON: keyof typeof Ionicons.glyphMap = "people";
// Session Flow toolbar - matches the reference design's colored icon-only
// buttons (green Attendance, blue Standard Test, amber Live Quiz, yellow
// Survey) rather than the app's other text+icon chip style.
export const MODULE_COLORS: Record<ModuleKey, string> = {
  standardTest: Colors.blueAccent,
  liveQuiz: Colors.warning,
  survey: "#FACC15",
};
export const ATTENDANCE_COLOR = Colors.success;
// Left-to-right order the toolbar icons appear in: Attendance, Live Quiz,
// Standard Test, Survey.
export const TOOLBAR_MODULE_ORDER: ModuleKey[] = ["liveQuiz", "standardTest", "survey"];
