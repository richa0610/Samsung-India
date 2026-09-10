/**
 * Centralized security violation type definitions.
 * Used by ProctoringPanel, SecurityViolationModal, and post_test.tsx.
 */

export const SECURITY_VIOLATIONS = {
  SIDE_LOOK: "SIDE-LOOK DETECTED",
  MULTIPLE_PEOPLE: "MULTIPLE PEOPLE DETECTED",
  NO_FACE: "NO FACE DETECTED",
  HEAD_TILT: "EXCESSIVE HEAD TILT",
  TAB_SWITCH: "TAB SWITCH DETECTED",
} as const;

export type SecurityViolationType =
  (typeof SECURITY_VIOLATIONS)[keyof typeof SECURITY_VIOLATIONS];

export const VIOLATION_FOOTER_LABELS: Record<SecurityViolationType, string> = {
  [SECURITY_VIOLATIONS.SIDE_LOOK]: "SIDE-LOOK\nDETECTED",
  [SECURITY_VIOLATIONS.MULTIPLE_PEOPLE]: "MULTIPLE PEOPLE\nDETECTED",
  [SECURITY_VIOLATIONS.NO_FACE]: "NO FACE\nDETECTED",
  [SECURITY_VIOLATIONS.HEAD_TILT]: "EXCESSIVE HEAD\nTILT",
  [SECURITY_VIOLATIONS.TAB_SWITCH]: "TAB SWITCH\nVIOLATION",
};

// Company-level defaults, overridden once real session data loads - see
// setProctoringSettings (called from useTraineeHome as soon as
// /sessions/current returns liveProctoringEnabled/proctoringMaxWarnings).
// `let` (not `const`) is deliberate: every consumer below reads these live
// via ES module bindings, so updating them here is reflected everywhere
// without threading a prop/config object through each file.
export let MAX_PROCTORING_WARNINGS = 3;
export let PROCTORING_ENABLED = true;

export function setProctoringSettings(enabled: boolean, maxWarnings: number): void {
  PROCTORING_ENABLED = enabled;
  MAX_PROCTORING_WARNINGS = maxWarnings > 0 ? maxWarnings : MAX_PROCTORING_WARNINGS;
}

// ─── Global session violation tracker ───────────────────────────────────────
// Persists the violation count per session key so that re-renders or navigations
// do not reset the count accidentally.
const sessionViolations: Record<
  string,
  { count: number; history: SecurityViolationType[]; locked: boolean; lastViolation?: SecurityViolationType }
> = {};

export function getSessionViolationCount(sessionId: string): number {
  return sessionViolations[sessionId]?.count ?? 0;
}

export function isSessionLocked(sessionId: string): boolean {
  return (
    sessionViolations[sessionId]?.locked === true ||
    (sessionViolations[sessionId]?.count ?? 0) >= MAX_PROCTORING_WARNINGS
  );
}

export function getLastViolation(
  sessionId: string,
): SecurityViolationType | null {
  return (
    sessionViolations[sessionId]?.lastViolation ??
    sessionViolations[sessionId]?.history[
      sessionViolations[sessionId].history.length - 1
    ] ??
    null
  );
}

export function lockSession(
  sessionId: string,
  violationType: SecurityViolationType,
): void {
  if (!sessionViolations[sessionId]) {
    sessionViolations[sessionId] = { count: MAX_PROCTORING_WARNINGS, history: [violationType], locked: true, lastViolation: violationType };
  } else {
    sessionViolations[sessionId].count = MAX_PROCTORING_WARNINGS;
    sessionViolations[sessionId].locked = true;
    sessionViolations[sessionId].lastViolation = violationType;
    sessionViolations[sessionId].history.push(violationType);
  }
}

export function recordSessionViolation(
  sessionId: string,
  violationType: SecurityViolationType,
): number {
  if (!sessionViolations[sessionId]) {
    sessionViolations[sessionId] = { count: 0, history: [], locked: false };
  }
  sessionViolations[sessionId].count = Math.min(
    sessionViolations[sessionId].count + 1,
    MAX_PROCTORING_WARNINGS,
  );
  sessionViolations[sessionId].lastViolation = violationType;
  sessionViolations[sessionId].history.push(violationType);
  if (sessionViolations[sessionId].count >= MAX_PROCTORING_WARNINGS) {
    sessionViolations[sessionId].locked = true;
  }
  return sessionViolations[sessionId].count;
}

export function resetSessionViolations(sessionId: string): void {
  delete sessionViolations[sessionId];
}
