import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { ExecutionFlowItem } from "@/api/training";
import ExecutionFlowRow from "./ExecutionFlowRow";

type ExecutionFlowModuleListProps = {
  modules: ExecutionFlowItem[];
  onRestart?: (moduleKey: string) => void;
  restartingModuleKey?: string | null;
  onViewTopPerformers?: (moduleKey: string) => void;
  onStart?: (moduleKey: string) => void;
  startingModuleKey?: string | null;
  hasStarted?: boolean;
};

export default function ExecutionFlowModuleList({
  modules,
  onRestart,
  restartingModuleKey,
  onViewTopPerformers,
  onStart,
  startingModuleKey,
  hasStarted = true,
}: ExecutionFlowModuleListProps) {
  if (modules.length === 0) {
    return <AppText style={styles.empty}>No modules configured for this session.</AppText>;
  }

  return (
    <View style={styles.list}>
      {modules.map((item) => (
        <ExecutionFlowRow
          key={item.moduleKey}
          item={item}
          hasStarted={hasStarted}
          onRestart={onRestart}
          onViewTopPerformers={onViewTopPerformers}
          onStart={onStart}
          isStarting={startingModuleKey === item.moduleKey}
          anyStarting={startingModuleKey != null}
          isRestarting={restartingModuleKey === item.moduleKey}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  list: { gap: 10 },
  empty: { fontSize: 12, color: "#6B7280", textAlign: "center", paddingVertical: 16 },
});
