import { ModuleConfig } from "@/api/training";
import { EvaluationModuleState } from "./useAddTrainingForm";

export const pad2 = (n: number) => String(n).padStart(2, "0");
export const formatDate = (d: Date) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
export const formatTime = (d: Date) => {
  let hours = d.getHours();
  const minutes = pad2(d.getMinutes());
  const suffix = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;
  return `${pad2(hours)}:${minutes} ${suffix}`;
};

// Display-only: the stored value stays YYYY-MM-DD (what the backend
// expects), but the reference UI shows dates as dd/mm/yyyy.
export function displayDate(value: string): string {
  const [y, m, d] = value.split("-");
  return y && m && d ? `${d}/${m}/${y}` : value;
}

// Parses the "hh:mm AM/PM" strings formatTime() produces into
// minutes-since-midnight, so module windows can be compared.
export function parseTimeToMinutes(value: string): number | null {
  const match = value.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!match) return null;
  let hours = Number(match[1]) % 12;
  if (match[3].toUpperCase() === "PM") hours += 12;
  return hours * 60 + Number(match[2]);
}

export function toPayloadModule(state: EvaluationModuleState): ModuleConfig {
  return {
    category: state.category,
    assessmentSuiteUid: state.assessmentSuiteUid,
    questionCount: state.questionCount ? Number(state.questionCount) : undefined,
    startTime: state.startTime,
    endTime: state.endTime,
    checkIn: state.checkIn,
    unlockCondition: state.unlockCondition,
  };
}
