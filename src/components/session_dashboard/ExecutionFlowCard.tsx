import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { AuditLogEntry, ExecutionFlowItem } from "@/api/training";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import AuditLogTable from "./AuditLogTable";
import ExecutionFlowModuleList from "./ExecutionFlowModuleList";

type ExecutionFlowCardProps = {
  executionFlow?: ExecutionFlowItem[];
  auditLog?: AuditLogEntry[];
  onRestartModule?: (moduleKey: string) => void;
  onViewTopPerformers?: (moduleKey: string) => void;
  onStartModule?: (moduleKey: string) => void;
  hasStarted?: boolean;
};

export default function ExecutionFlowCard({
  executionFlow = [],
  auditLog = [],
  onRestartModule,
  onViewTopPerformers,
  onStartModule,
  hasStarted = true,
}: ExecutionFlowCardProps) {
  const [activeTab, setActiveTab] = useState<"flow" | "logs">("flow");

  return (
    <View style={styles.card}>
      {/* Tabs Header: EXECUTION FLOW | Audit Logs */}
      <View style={styles.tabsHeader}>
        <Pressable
          style={[styles.tab, activeTab === "flow" && styles.tabActive]}
          onPress={() => setActiveTab("flow")}
        >
          <Ionicons
            name="swap-horizontal-outline"
            size={14}
            color={activeTab === "flow" ? "#2563EB" : "#6B7280"}
          />
          <AppText style={[styles.tabText, activeTab === "flow" && styles.tabTextActive]}>
            EXECUTION FLOW
          </AppText>
        </Pressable>

        <Pressable
          style={[styles.tab, activeTab === "logs" && styles.tabActive]}
          onPress={() => setActiveTab("logs")}
        >
          <Ionicons
            name="shield-checkmark-outline"
            size={14}
            color={activeTab === "logs" ? "#2563EB" : "#6B7280"}
          />
          <AppText style={[styles.tabText, activeTab === "logs" && styles.tabTextActive]}>
            Audit Logs
          </AppText>
        </Pressable>
      </View>

      {activeTab === "flow" ? (
        <ExecutionFlowModuleList
          modules={executionFlow}
          onRestart={onRestartModule}
          onViewTopPerformers={onViewTopPerformers}
          onStart={onStartModule}
          hasStarted={hasStarted}
        />
      ) : (
        <AuditLogTable entries={auditLog} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.card,
  },
  tabsHeader: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
    paddingBottom: 4,
    marginBottom: 8,
  },
  tab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 6,
    borderBottomWidth: 2,
    borderBottomColor: "transparent",
  },
  tabActive: { borderBottomColor: "#2563EB" },
  tabText: { fontSize: 11, fontWeight: "600", color: "#6B7280" },
  tabTextActive: { color: "#2563EB", fontWeight: "700" },
});
