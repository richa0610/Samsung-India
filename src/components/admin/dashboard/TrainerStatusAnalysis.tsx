import { ScrollView, StyleSheet, View } from "react-native";

import { TrainerStatusSection } from "@/api/admin";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type TrainerStatusAnalysisProps = {
  data?: TrainerStatusSection[];
};

export default function TrainerStatusAnalysis({ data }: TrainerStatusAnalysisProps) {
  // "Completed" isn't shown, zero-count rows are hidden (and any section left
  // empty), and with nothing to show the panel renders nothing at all.
  const sections = (data ?? [])
    .filter((s) => s.title.trim().toLowerCase() !== "completed")
    .map((s) => ({ ...s, items: s.items.filter((item) => item.count > 0) }))
    .filter((s) => s.items.length > 0);

  if (sections.length === 0) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        nestedScrollEnabled
        showsVerticalScrollIndicator
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
      >
        {sections.map((section, sIdx) => (
          <View key={`${section.title}-${sIdx}`} style={styles.sectionBlock}>
            <View style={styles.headerBar}>
              <AppText style={styles.headerTitle} weight={FontWeight.bold}>
                {section.title}
              </AppText>
            </View>

            {section.items.map((item, iIdx) => (
              <View
                key={`${item.label}-${iIdx}`}
                style={[
                  styles.itemRow,
                  iIdx === section.items.length - 1 && styles.itemRowLast,
                ]}
              >
                <AppText style={styles.itemLabel}>{item.label}</AppText>
                <View style={styles.badge}>
                  <AppText style={styles.badgeText} weight={FontWeight.bold}>
                    {item.count}
                  </AppText>
                </View>
              </View>
            ))}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.gray200,
    backgroundColor: Colors.white,
    overflow: "hidden",
  },
  emptyContainer: {
    marginTop: 10,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.gray200,
    backgroundColor: Colors.gray50,
    paddingVertical: 18,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyText: {
    fontSize: 12,
    textAlign: "center",
  },
  scrollArea: {
    maxHeight: 180,
  },
  scrollContent: {
    paddingBottom: 2,
  },
  sectionBlock: {
    width: "100%",
  },
  headerBar: {
    backgroundColor: Colors.slate200,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  headerTitle: {
    color: Colors.gray700,
    fontSize: 13.5,
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    backgroundColor: Colors.white,
  },
  itemRowLast: {
    borderBottomColor: "transparent",
  },
  itemLabel: {
    fontSize: 13,
    color: Colors.gray600,
  },
  badge: {
    backgroundColor: Colors.slate100,
    borderRadius: 6,
    minWidth: 26,
    height: 22,
    paddingHorizontal: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    fontSize: 12.5,
    color: Colors.gray800,
  },
});
