import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { SelectOption } from "@/components/ui/SearchableSelect";

export const ICON_BADGE_BG = "#E3ECFF";

export const COMPANY_OPTIONS: SelectOption[] = [{ label: "Samsung India", value: "Samsung India" }];

export const REQUESTED_BY_OPTIONS: SelectOption[] = [
  { label: "Quess Corp Ltd", value: "Quess Corp Ltd" },
  { label: "Other", value: "Other" },
];

// Zone / Region, State / District, Audience, Session Type, Training Type and Training Hub pickers
// have no static option list - they're populated from the /admin catalog endpoints (the master
// list's categories, or the values past trainings used where there is no category).

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
