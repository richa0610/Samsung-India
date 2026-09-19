import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { TrainingModuleDetail } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import QuestionReviewItem from "./QuestionReviewItem";
import { statusMetaFor } from "./statusMeta";

const MODULE_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  ATTENDANCE: "person-outline",
  STANDARD_TEST: "document-text-outline",
  LIVE_QUIZ: "flash-outline",
  SURVEY: "clipboard-outline",
};

type ModuleDetailCardProps = {
  module: TrainingModuleDetail;
  expanded: boolean;
  onToggle: () => void;
};

export default function ModuleDetailCard({ module, expanded, onToggle }: ModuleDetailCardProps) {
  const meta = statusMetaFor(module.status);
  const hasQuestions = module.questions.length > 0;
  const correctCount = module.questions.filter((q) => q.isCorrect).length;

  return (
    <View style={styles.card}>
      <Pressable
        style={styles.header}
        onPress={hasQuestions ? onToggle : undefined}
        accessibilityRole={hasQuestions ? "button" : undefined}
        accessibilityLabel={hasQuestions ? `${module.name}, tap to ${expanded ? "collapse" : "expand"}` : module.name}
      >
        <View style={styles.iconWrap}>
          <Ionicons name={MODULE_ICONS[module.key] ?? "layers-outline"} size={17} color="#2563EB" />
        </View>

        <View style={styles.titleColumn}>
          <AppText variant="body" weight={FontWeight.bold} color="#111827">
            {module.name}
          </AppText>
          {module.completedAt && (
            <AppText variant="tiny" color="#6B7280">
              {module.completedAt}
            </AppText>
          )}
        </View>

        {module.score && (
          <AppText variant="caption" weight={FontWeight.bold} color="#111827" style={styles.scoreText}>
            {module.score}
          </AppText>
        )}

        <View style={[styles.statusPill, { backgroundColor: meta.bg }]}>
          <Ionicons name={meta.icon} size={13} color={meta.color} />
          <AppText variant="tiny" weight={FontWeight.bold} color={meta.color}>
            {module.status}
          </AppText>
        </View>

        {hasQuestions && <Ionicons name={expanded ? "chevron-up" : "chevron-down"} size={18} color="#9CA3AF" />}
      </Pressable>

      {hasQuestions && expanded && (
        <View style={styles.questionsBlock}>
          <AppText variant="tiny" color="#6B7280" style={styles.summaryLine}>
            {correctCount}/{module.questions.length} correct
          </AppText>
          {module.questions.map((attempt, index) => (
            <QuestionReviewItem key={attempt.id} index={index + 1} attempt={attempt} />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginBottom: 12,
    overflow: "hidden",
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  iconWrap: {
    width: 30,
    height: 30,
    borderRadius: 8,
    backgroundColor: "#EFF6FF",
    alignItems: "center",
    justifyContent: "center",
  },
  titleColumn: { flex: 1, gap: 2 },
  scoreText: { marginRight: 2 },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: Radius.pill,
  },
  questionsBlock: {
    paddingHorizontal: 14,
    paddingBottom: 12,
  },
  summaryLine: { marginBottom: 2 },
});
