import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

type QuickActionsCardProps = {
  onCreateTraining: () => void;
  onTrainingList: () => void;
  onViewReports: () => void;
  onAddTrainee: () => void;
};

export default function QuickActionsCard({
  onCreateTraining,
  onTrainingList,
  onViewReports,
  onAddTrainee,
}: QuickActionsCardProps) {
  const actions = [
    {
      title: "Create New Training",
      iconName: "add-circle" as const,
      color: "#0066FF",
      bg: "#EFF6FF",
      onPress: onCreateTraining,
    },
    {
      title: "Training List",
      iconName: "clipboard" as const,
      color: "#10B981",
      bg: "#ECFDF5",
      onPress: onTrainingList,
    },
    {
      title: "View Reports",
      iconName: "document-text" as const,
      color: "#F59E0B",
      bg: "#FFFBEB",
      onPress: onViewReports,
    },
    {
      title: "Add New Trainee",
      iconName: "people" as const,
      color: "#8B5CF6",
      bg: "#F5F3FF",
      onPress: onAddTrainee,
    },
  ];

  return (
    <View style={styles.card}>
      <AppText style={styles.headerTitle}>Quick Actions</AppText>

      <View style={styles.actionsList}>
        {actions.map((action) => (
          <Pressable
            key={action.title}
            style={[styles.actionRow, { backgroundColor: action.bg }]}
            onPress={action.onPress}
          >
            <View style={styles.leftContent}>
              <Ionicons name={action.iconName} size={13} color={action.color} />
              <AppText style={styles.actionText} numberOfLines={1}>
                {action.title}
              </AppText>
            </View>
            <Ionicons name="chevron-forward" size={10} color={action.color} />
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 8,
    ...Shadows.card,
  },
  headerTitle: {
    fontSize: 10.5,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 6,
  },
  actionsList: {
    gap: 10,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 5,
    paddingHorizontal: 5,
    borderRadius: 6,
  },
  leftContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    flex: 1,
  },
  actionText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#1F2937",
    flex: 1,
  },
});
