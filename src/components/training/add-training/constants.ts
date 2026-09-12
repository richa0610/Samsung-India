import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { SelectOption } from "@/components/ui/SearchableSelect";

export const ICON_BADGE_BG = "#E3ECFF";

export const REGIONS_BY_ZONE: Record<string, string[]> = {
  "North Zone": ["North 1", "North 2", "North 3", "North 4"],
  "South Zone": ["South 1", "South 2", "South 3", "South 4", "South 1 [KR]", "South 1 [TN]"],
  "East Zone": ["East 1", "East 2", "East 3", "East 4"],
  "West Zone": ["West 1", "West 2", "West 3", "West 4"],
};
export const ZONES = Object.keys(REGIONS_BY_ZONE);

export const COMPANY_OPTIONS: SelectOption[] = [{ label: "Samsung India", value: "Samsung India" }];

export const REQUESTED_BY_OPTIONS: SelectOption[] = [
  { label: "Quess Corp Ltd", value: "Quess Corp Ltd" },
  { label: "Other", value: "Other" },
];

export const TRAINER_OPTIONS: SelectOption[] = [
  { label: "2002641904 - Bejoyendra Kolay", value: "2002641904" },
  { label: "2002035871 - Bharat Kumar Vaswani", value: "2002035871" },
  { label: "GS20356576 - Bharath Jain", value: "GS20356576" },
  { label: "2003932855 - CHAGI VARAPRASAD", value: "2003932855" },
  { label: "9646499023 - CHANDAN SHARMA", value: "9646499023" },
  { label: "2003907196 - CHETHAN KUMAR R", value: "2003907196" },
  { label: "GS20402359 - CHINMAYA K", value: "GS20402359" },
  { label: "AGTM2620011 - Demo Trainer", value: "demotrainer" },
  { label: "2003250416 - Devendra Kumar", value: "2003250416" },
  { label: "2003628340 - Dharmeshkumar Patel", value: "2003628340" },
  { label: "2003385218 - Dinesh Singh Rathore", value: "2003385218" },
  { label: "2002035876 - Eric Keki Patel", value: "2002035876" },
  { label: "9562267076 - FIRDOUS FAYAS", value: "9562267076" },
  { label: "7259635514 - Gajendra", value: "7259635514" },
  { label: "9585478000 - GANESH", value: "9585478000" },
];

// Training Hub / Audience / Session Type / Training Type pickers have no
// static option list - they're populated from the /admin catalog endpoints
// (distinct values this tenant has used on past trainings).

export const UNLOCK_CONDITIONS = ["Automatic", "Manual Broadcast"];

export const DEFAULT_CATEGORY_OPTIONS: SelectOption[] = ["POST TEST", "SAMSUMG S25", "Survey", "Quiz"].map((v) => ({
  label: v,
  value: v,
}));

// Stable, length-capped UID for a placeholder question set. `assessment_results.
// assessmentSuiteUid` is varchar(50) in the real schema, so the raw
// `default:<full name>` (up to 52 chars) overflowed it on submit. The Python
// side (`scripts/seed_default_question_sets.py`) must produce the identical
// string.
export const questionSetUid = (name: string) =>
  `default:${name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40)
    .replace(/-+$/, "")}`;

export const DEFAULT_QUESTION_SET_OPTIONS: Record<string, SelectOption[]> = {
  "POST TEST": [
    "S26 Review meeting",
    "Samsung Test 1",
    "Samsung Test 2",
    "MX-Training Offline Post Training For June 26",
    "Laptop Classroom/Webinar: Post Test June 26",
    "MX-Training Offline Post Test (July'26)",
    "Laptop Classroom/Webinar: Post Test July'26",
  ].map((name) => ({ label: name, value: questionSetUid(name) })),
};

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
  standardTest: "#2563EB",
  liveQuiz: "#F59E0B",
  survey: "#FACC15",
};
export const ATTENDANCE_COLOR = Colors.success;
// Left-to-right order the toolbar icons appear in: Attendance, Live Quiz,
// Standard Test, Survey.
export const TOOLBAR_MODULE_ORDER: ModuleKey[] = ["liveQuiz", "standardTest", "survey"];
