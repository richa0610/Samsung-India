import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { TrainingModuleDetail } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { trainingStatusLabel } from "@/utils/trainingStatusLabel";
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
  onRetest?: () => void;
};

export default function ModuleDetailCard({ module, expanded, onToggle, onRetest }: ModuleDetailCardProps) {
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
          <Ionicons name={MODULE_ICONS[module.key] ?? "layers-outline"} size={17} color={Colors.blueAccent} />
        </View>

        <View style={styles.titleColumn}>
          <AppText variant="body" weight={FontWeight.bold} color={Colors.black}>
            {module.name}
          </AppText>
          {module.completedAt && (
            <AppText variant="tiny" color={Colors.gray500}>
              {module.completedAt}
            </AppText>
          )}
        </View>

        {module.score && (
          <AppText variant="caption" weight={FontWeight.bold} color={Colors.black} style={styles.scoreText}>
            {module.score}
          </AppText>
        )}

        <View style={styles.statusGroup}>
          {module.canRetest && onRetest && (
            <Pressable
              style={styles.retestBtn}
              onPress={(e) => {
                e?.stopPropagation?.();
                onRetest();
              }}
              hitSlop={6}
              accessibilityRole="button"
              accessibilityLabel={`Retest ${module.name}`}
            >
              <Ionicons name="reload-outline" size={12} color={Colors.white} />
              <AppText variant="tiny" weight={FontWeight.bold} color={Colors.white}>
                Retest
              </AppText>
            </Pressable>
          )}

          {module.retestDone ? (
            <View style={styles.retestDonePill}>
              <Ionicons name="checkmark-done" size={13} color={Colors.successTeal} />
              <AppText variant="tiny" weight={FontWeight.bold} color={Colors.successTeal}>
                {module.retestScore ? `Retest: ${module.retestScore}` : "Retested"}
              </AppText>
            </View>
          ) : (
            <View style={[styles.statusPill, { backgroundColor: meta.bg }]}>
              <Ionicons name={meta.icon} size={13} color={meta.color} />
              <AppText variant="tiny" weight={FontWeight.bold} color={meta.color}>
                {trainingStatusLabel(module.status)}
              </AppText>
            </View>
          )}
        </View>

        {hasQuestions && <Ionicons name={expanded ? "chevron-up" : "chevron-down"} size={18} color={Colors.gray400} />}
      </Pressable>

      {hasQuestions && expanded && (
        <View style={styles.questionsBlock}>
          <AppText variant="tiny" color={Colors.gray500} style={styles.summaryLine}>
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
    borderColor: Colors.gray200,
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
    backgroundColor: Colors.blue50,
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
  statusGroup: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  retestBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.mainColour1,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: Radius.pill,
  },
  retestDonePill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.successBgSoft,
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
