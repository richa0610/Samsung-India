import { Ionicons } from "@expo/vector-icons";

export const MAX_WARNINGS = 3;

export const RULES = [
  "Sit facing the camera",
  "Keep your face fully visible",
  "Ensure good lighting",
  "Stay alone during the test",
];

export type PoseRow = {
  key: string;
  ok: boolean;
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
};

export const POSE_ROWS: PoseRow[] = [
  { key: "forward", ok: true, icon: "person", label: "Face looking forward" },
  { key: "left", ok: false, icon: "arrow-back", label: "Face turned left" },
  { key: "right", ok: false, icon: "arrow-forward", label: "Face turned right" },
  { key: "up", ok: false, icon: "arrow-up", label: "Looking up" },
  { key: "down", ok: false, icon: "arrow-down", label: "Looking down" },
  { key: "multiple", ok: false, icon: "people", label: "Multiple people detected" },
];
