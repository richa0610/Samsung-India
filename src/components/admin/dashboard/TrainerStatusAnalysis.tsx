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
  const sections = data ?? [];

  if (sections.length === 0 || sections.every((s) => s.items.length === 0)) {
    return (
      <View style={styles.emptyContainer}>
        <AppText style={styles.emptyText} color={Colors.gray600}>
          No status analysis records found
        </AppText>
      </View>
    );
  }

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
    borderColor: "#E5E7EB",
    backgroundColor: Colors.white,
    overflow: "hidden",
  },
  emptyContainer: {
    marginTop: 10,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    backgroundColor: "#F9FAFB",
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
    backgroundColor: "#E2E8F0",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  headerTitle: {
    color: "#374151",
    fontSize: 13.5,
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
    backgroundColor: Colors.white,
  },
  itemRowLast: {
    borderBottomColor: "transparent",
  },
  itemLabel: {
    fontSize: 13,
    color: "#4B5563",
  },
  badge: {
    backgroundColor: "#F1F5F9",
    borderRadius: 6,
    minWidth: 26,
    height: 22,
    paddingHorizontal: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    fontSize: 12.5,
    color: "#1F2937",
  },
});
