import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { AttendanceModuleCard } from "./AttendanceModuleCard";
import {
  ATTENDANCE_COLOR,
  ATTENDANCE_ICON,
  MODULE_COLORS,
  MODULE_ICONS,
  ModuleKey,
  TOOLBAR_MODULE_ORDER,
} from "./constants";
import { ModuleCard } from "./ModuleCard";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

function ToolChip({ icon, color, active, onPress }: {
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.toolChip, active && { backgroundColor: color, borderColor: color }]}
      onPress={onPress}
    >
      <Ionicons name={icon} size={18} color={active ? Colors.white : color} />
    </Pressable>
  );
}

export function SessionFlowSection({ form }: { form: AddTrainingForm }) {
  const items = form.orderedFlowItems;

  return (
    <AppCard style={styles.card}>
      <SectionTitle index={4} title="Session Flow" icon="git-branch-outline" />

      <View style={styles.toolbar}>
        <ToolChip
          icon={ATTENDANCE_ICON}
          color={ATTENDANCE_COLOR}
          active={form.attendanceEnabled}
          onPress={form.toggleAttendance}
        />
        {TOOLBAR_MODULE_ORDER.map((key) => (
          <ToolChip
            key={key}
            icon={MODULE_ICONS[key]}
            color={MODULE_COLORS[key]}
            active={form.modules[key].enabled}
            onPress={() => form.toggleModule(key)}
          />
        ))}
      </View>
      <View style={styles.toolbarDivider} />

      {items.length === 0 ? (
        <View style={styles.emptyFlow}>
          <View style={styles.emptyFlowIconRing}>
            <Ionicons name="arrow-up" size={18} color={Colors.gray400} />
          </View>
          <AppText style={styles.emptyFlowText} color={Colors.gray600}>
            Select a module from the toolbar above to start building your session flow.
          </AppText>
        </View>
      ) : (
        items.map((item) =>
          item.id === "attendance" ? (
            <AttendanceModuleCard key="attendance" form={form} />
          ) : (
            <ModuleCard key={item.id} moduleKey={item.id as ModuleKey} form={form} />
          ),
        )
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  toolbar: {
    flexDirection: "row",
    alignSelf: "center",
    alignItems: "center",
    gap: 22,
    paddingHorizontal: 22,
    paddingVertical: 10,
    marginBottom: 14,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.pill,
  },
  toolChip: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    borderColor: "transparent",
    alignItems: "center",
    justifyContent: "center",
  },
  toolbarDivider: { height: 1, backgroundColor: Colors.gray200, marginBottom: 14 },
  emptyFlow: { alignItems: "center", gap: 10, paddingVertical: 28, backgroundColor: Colors.gray100, borderRadius: Radius.xl },
  emptyFlowIconRing: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderStyle: "dashed",
    borderColor: Colors.gray400,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyFlowText: { fontSize: Fonts.bodySm, textAlign: "center", paddingHorizontal: 24 },
});
