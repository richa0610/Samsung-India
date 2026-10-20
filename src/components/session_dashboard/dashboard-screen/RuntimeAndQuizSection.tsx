import { Fragment } from "react";

import { SessionDashboard } from "@/api/training";
import ActiveModuleCard from "@/components/session_dashboard/ActiveModuleCard";
import SessionRuntimeCard from "@/components/session_dashboard/SessionRuntimeCard";
import { formatDurationHM } from "./formatting";

type RuntimeAndQuizSectionProps = {
  data: SessionDashboard | null;
  actualRuntime?: string;
  // Same live-ticking, module-active-only seconds behind `actualRuntime`
  // (frozen during a gap between modules) - drives "Consumed" and the
  // "Total Time Used" gauge below, so a session sitting idle between
  // modules doesn't look like it's burning through its assigned budget.
  runtimeSeconds?: number | null;
  onStopActiveModule: () => void;
};

export default function RuntimeAndQuizSection({
  data,
  actualRuntime,
  runtimeSeconds,
  onStopActiveModule,
}: RuntimeAndQuizSectionProps) {
  const flow = data?.executionFlow ?? [];
  const active = flow.find((m) => m.moduleKey === data?.activeModuleId) ?? null;

  // Live progress across this session's configured modules: how many of the
  // flow's modules have finished vs. how many it contains.
  const completedModules = flow.filter((m) => m.status === "Completed").length;
  const moduleCompletionPercent = flow.length
    ? Math.round((completedModules / flow.length) * 100)
    : 0;

  // "Assigned" = planned budget: the sum of every module's configured
  // start -> end window (backend `assignedMinutes`).
  const assignedSeconds = flow.reduce((sum, m) => sum + (m.assignedMinutes ?? 0) * 60, 0);
  // "Consumed" = the same module-active-only runtime as "Actual Session
  // Runtime" (frozen during a gap between modules) - NOT raw wall-clock time
  // since the session opened. A session sitting idle between modules (no
  // module running yet, or a pause after one ends) shouldn't make "Total
  // Time Used" climb as if the assigned budget were being burned.
  const consumedSeconds = runtimeSeconds ?? 0;
  const timeUsedPercent = assignedSeconds
    ? Math.min(100, Math.round((consumedSeconds / assignedSeconds) * 100))
    : 0;

  return (
    <Fragment>
      <SessionRuntimeCard
        actualRuntime={actualRuntime}
        assignedTime={formatDurationHM(assignedSeconds)}
        consumedTime={formatDurationHM(consumedSeconds)}
        timeUsedPercent={timeUsedPercent}
        moduleCompletionPercent={moduleCompletionPercent}
      />

      {active && (
        <ActiveModuleCard
          moduleLabel={active.label}
          startedAt={active.startedAt}
          questionCount={data?.activeModuleQuestionCount ?? null}
          onEndModule={onStopActiveModule}
        />
      )}
    </Fragment>
  );
}
