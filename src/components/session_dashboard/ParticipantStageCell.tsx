import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import type { ParticipantModuleProgress } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";

type ParticipantStageCellProps = {
  stage: string;
  modules: ParticipantModuleProgress[];
};

/** The Participant Master List's Stage cell: the participant's attendance stage under a pin
 *  ("Attendance" / "Not Started"), then a green tick / red cross chip per activity after
 *  Attendance (done / not yet). */
export default function ParticipantStageCell({ stage, modules }: ParticipantStageCellProps) {
  return (
    <View style={styles.cell}>
      <View style={styles.stageRow}>
        <Ionicons name="location" size={10} color={Colors.brandBlue} />
        <AppText style={styles.stageText} numberOfLines={1}>
          {stage}
        </AppText>
      </View>
      {modules.length > 0 && (
        <View style={styles.chips}>
          {modules.map((module) => (
            <View
              key={module.key}
              style={[styles.chip, module.done ? styles.chipDone : styles.chipTodo]}
              accessible
              accessibilityLabel={`${module.label}: ${module.done ? "done" : "not done"}`}
            >
              <Ionicons
                name={module.done ? "checkmark-circle" : "close-circle"}
                size={9}
                color={module.done ? Colors.statusGreen : Colors.red}
              />
              <AppText style={[styles.chipText, { color: module.done ? Colors.statusGreen : Colors.red }]}>
                {module.label}
              </AppText>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  // Centred in the column, like the rest of the list.
  cell: { gap: 2, alignItems: "center" },
  stageRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 2 },
  stageText: { fontSize: 9, fontWeight: "700", color: Colors.brandBlue, flexShrink: 1 },
  chips: { flexDirection: "row", flexWrap: "wrap", justifyContent: "center", gap: 2 },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 1.5,
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 2.5,
    paddingVertical: 1,
  },
  chipDone: { backgroundColor: Colors.successBgSoft, borderColor: Colors.statusGreen },
  chipTodo: { backgroundColor: Colors.dangerBgSoft, borderColor: Colors.red },
  chipText: { fontSize: 8, fontWeight: "700" },
});
