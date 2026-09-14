import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { ExecutionFlowItem } from "@/api/training";
import ExecutionFlowRow from "./ExecutionFlowRow";

type ExecutionFlowModuleListProps = {
  modules: ExecutionFlowItem[];
  onRestart?: (moduleKey: string) => void;
  onViewTopPerformers?: (moduleKey: string) => void;
  onStart?: (moduleKey: string) => void;
  hasStarted?: boolean;
};

export default function ExecutionFlowModuleList({
  modules,
  onRestart,
  onViewTopPerformers,
  onStart,
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
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  list: { gap: 10 },
  empty: { fontSize: 12, color: "#6B7280", textAlign: "center", paddingVertical: 16 },
});
