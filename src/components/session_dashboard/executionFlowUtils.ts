import { Ionicons } from "@expo/vector-icons";

import { ExecutionFlowStatus } from "@/api/training";

export type ModuleVisual = {
  icon: keyof typeof Ionicons.glyphMap;
  bg: string;
  categoryLabel: string;
};

const MODULE_VISUALS: Record<string, ModuleVisual> = {
  ATTENDANCE: { icon: "people", bg: "#16A34A", categoryLabel: "ATTENDANCE" },
  LIVE_QUIZ: { icon: "rocket", bg: "#2563EB", categoryLabel: "QUIZ" },
  STANDARD_TEST: { icon: "clipboard", bg: "#374151", categoryLabel: "TEST" },
  SURVEY: { icon: "chatbubble-ellipses", bg: "#D97706", categoryLabel: "SURVEY" },
};

const FALLBACK_VISUAL: ModuleVisual = { icon: "layers", bg: "#6B7280", categoryLabel: "MODULE" };

export function getModuleVisual(moduleKey: string): ModuleVisual {
  return MODULE_VISUALS[moduleKey] ?? FALLBACK_VISUAL;
}

export type StatusPresentation = {
  label: string;
  bg: string;
  color: string;
};

export function getExecutionStatusPresentation(status: ExecutionFlowStatus): StatusPresentation {
  if (status === "Completed") return { label: "Executed", bg: "#D1FAE5", color: "#059669" };
  if (status === "Running") return { label: "Running", bg: "#FEE2E2", color: "#DC2626" };
  return { label: "Pending", bg: "#FEF3C7", color: "#B45309" };
}

export function formatElapsed(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return hours > 0 ? `${hours}h ${minutes}m ${seconds}s` : `${minutes}m ${seconds}s`;
}
