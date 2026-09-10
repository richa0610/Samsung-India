import { Fragment } from "react";

import { SessionDashboard } from "@/api/training";
import ActiveModuleCard from "@/components/session_dashboard/ActiveModuleCard";
import SessionRuntimeCard from "@/components/session_dashboard/SessionRuntimeCard";
import { useLiveRuntime } from "@/hooks/useLiveRuntime";
import { formatDurationHM } from "./formatting";

type RuntimeAndQuizSectionProps = {
  data: SessionDashboard | null;
  actualRuntime?: string;
  onStopActiveModule: () => void;
};

export default function RuntimeAndQuizSection({
  data,
  actualRuntime,
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
  // "Consumed" = wall-clock time the session has actually been open
  // (actualStartedAt -> now / ended, gaps between modules included), ticking
  // live while it runs - distinct from "Actual Session Runtime" above, which
  // counts module-active time only.
  const consumedSeconds = useLiveRuntime(data?.actualStartedAt, data?.actualEndedAt);
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
