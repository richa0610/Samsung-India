import { StyleSheet, View } from "react-native";

import ProctoringPanel from "@/components/proctoring/OnDeviceProctoringPanel";
import { SecurityViolationType } from "@/components/proctoring/violations";
import TimeProgress from "@/components/ui/TimeProgress";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";

type TestProgressRowProps = {
  totalMinutes: number;
  remainingMinutes: number;
  remainingSecondsPart: number;
  token: string | null;
  isActive: boolean;
  paused: boolean;
  violationCount: number;
  currentViolation: SecurityViolationType | null;
  onViolation: (violationType: SecurityViolationType) => void;
  onWarning: (violationType: SecurityViolationType) => void;
};

export default function TestProgressRow({
  totalMinutes,
  remainingMinutes,
  remainingSecondsPart,
  token,
  isActive,
  paused,
  violationCount,
  currentViolation,
  onViolation,
  onWarning,
}: TestProgressRowProps) {
  return (
    <View style={styles.timerProctorRow}>
      <View style={styles.timerColumn}>
        <TimeProgress
          totalMinutes={totalMinutes}
          remainingMinutes={remainingMinutes}
          remainingSeconds={remainingSecondsPart}
          size={120}
        />
      </View>
      <View style={styles.proctorColumn}>
        <ProctoringPanel
          token={token}
          active={isActive}
          paused={paused}
          warningsCount={violationCount}
          latestViolation={currentViolation}
          onViolation={onViolation}
          onWarning={onWarning}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  timerProctorRow: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 2, blur: 8, opacity: 0.06, elevation: 2 }),
  },
  timerColumn: { flex: 1, alignItems: "center", justifyContent: "center" },
  proctorColumn: { flex: 1, alignItems: "center", justifyContent: "center" },
});
