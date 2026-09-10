import { useEffect, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet } from "react-native";

import { SessionDashboard } from "@/api/training";
import { LiveQuizControls } from "@/components/session_dashboard/sessionDashboardTypes";
import {
  AssessmentResultCard,
  AudienceBreakdownCard,
  ExecutionFlowCard,
  SessionDetailsCard,
  SessionHeroesCard,
  TopPerformersCard,
} from "@/components/session_dashboard";
import { Colors } from "@/theme/colors";
import { formatDurationHMS, formatRuntimeLabel } from "./formatting";
import LiveStudioSection from "./LiveStudioSection";
import { participantsFromTrainees } from "./participantMapper";
import RuntimeAndQuizSection from "./RuntimeAndQuizSection";

type DashboardScrollContentProps = {
  data: SessionDashboard | null;
  isSessionClosed: boolean;
  showSessionData: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  onStartModule: (moduleKey: string) => void;
  onStopActiveModule: () => void;
  onRestartModule: (moduleKey: string) => void;
  onMarkAttendance: (traineeUid: string, status: "Present" | "Absent", reason: string) => void;
  onUnlockExam: (traineeUid: string, reason: string) => void;
  liveQuizControls: LiveQuizControls;
};

export default function DashboardScrollContent({
  data,
  isSessionClosed,
  showSessionData,
  refreshing,
  onRefresh,
  onStartModule,
  onStopActiveModule,
  onRestartModule,
  onMarkAttendance,
  onUnlockExam,
  liveQuizControls,
}: DashboardScrollContentProps) {
  // Server-authoritative sum of each module's own active time (see
  // _module_active_seconds on the backend) - ticks locally only while a
  // module is actually live, so it doesn't drift ahead of the real value
  // during a gap between modules (unlike the previous raw
  // actualStartedAt/actualEndedAt wall-clock diff, which counted those
  // gaps as runtime too).
  const [runtimeSeconds, setRuntimeSeconds] = useState<number | null>(data?.runtimeSeconds ?? null);
  useEffect(() => {
    const moduleRunning = data?.conferenceStatus === "Ongoing" && data?.activeModuleId != null;
    if (!moduleRunning || data?.runtimeSeconds == null) {
      setRuntimeSeconds(data?.runtimeSeconds ?? null);
      return;
    }
    const base = data.runtimeSeconds;
    const capturedAt = Date.now();
    const tick = () => setRuntimeSeconds(base + Math.floor((Date.now() - capturedAt) / 1000));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [data?.runtimeSeconds, data?.conferenceStatus, data?.activeModuleId]);

  const participants = participantsFromTrainees(data?.trainees ?? []);

  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />
      }
    >
      <SessionDetailsCard
        topic={data?.trainingType || "Webinar"}
        date={data?.conferenceDate || "20 Jul 2026"}
        trainerName={data?.trainerName || "Demo Trainer"}
        runtime={formatRuntimeLabel(runtimeSeconds)}
        conferenceStatus={data?.conferenceStatus || "Scheduled"}
      />

      <AudienceBreakdownCard
        totalAudience={data?.audience?.total ?? 0}
        present={data?.audience?.present ?? 0}
        notMarked={data?.audience?.notMarked ?? 0}
        absent={data?.audience?.absent ?? 0}
        assigned={data?.audience?.assigned ?? 0}
        unassigned={data?.audience?.unassigned ?? 0}
        fresh={data?.audience?.fresh ?? 0}
        hasStarted={showSessionData}
      />

      <AssessmentResultCard
        passCount={data?.assessment?.pass ?? 0}
        failCount={data?.assessment?.fail ?? 0}
        totalAttempts={data?.assessment?.totalAttempts ?? 0}
        passRate={
          data?.assessment?.totalAttempts
            ? Math.round((data.assessment.pass / data.assessment.totalAttempts) * 100)
            : 0
        }
        hasStarted={showSessionData}
      />

      <TopPerformersCard
        performers={(data?.topPerformers ?? []).map((p) => ({
          id: p.traineeUid,
          name: p.name,
          score: Math.round(p.score),
          maxScore: Math.round(p.maxScore),
          percentage: Math.round(p.percentage),
        }))}
        hasStarted={showSessionData}
      />

      <SessionHeroesCard
        heroes={data?.sessionHeroes ?? []}
        isSessionClosed={isSessionClosed}
        hasStarted={showSessionData}
      />

      {showSessionData && (
        <RuntimeAndQuizSection
          data={data}
          actualRuntime={formatDurationHMS(runtimeSeconds)}
          onStopActiveModule={onStopActiveModule}
        />
      )}

      <ExecutionFlowCard
        executionFlow={data?.executionFlow ?? []}
        auditLog={data?.auditLog ?? []}
        hasStarted={showSessionData}
        onStartModule={onStartModule}
        onRestartModule={onRestartModule}
      />

      {showSessionData && (
        <LiveStudioSection
          participants={participants}
          liveStudio={data?.liveStudio ?? null}
          liveQuizControls={liveQuizControls}
          onRefresh={onRefresh}
          canEditAttendance={data?.conferenceStatus === "Ongoing"}
          onMarkAttendance={onMarkAttendance}
          onUnlockExam={onUnlockExam}
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 20,
  },
});
