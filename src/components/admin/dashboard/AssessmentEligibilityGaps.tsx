import { ScrollView, StyleSheet, View } from "react-native";

import { AssessmentGapSection } from "@/api/admin";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type AssessmentEligibilityGapsProps = {
  data?: AssessmentGapSection[];
};

export default function AssessmentEligibilityGaps({ data }: AssessmentEligibilityGapsProps) {
  const sections = data ?? [];

  if (sections.length === 0 || sections.every((s) => s.items.length === 0)) return null;

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
            <View style={styles.sectionHeader}>
              <AppText style={styles.sectionTitle} weight={FontWeight.bold}>
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
                <AppText style={styles.itemLabel} color={Colors.gray600}>
                  {item.label}
                </AppText>
                <View style={styles.badge}>
                  <AppText
                    style={[
                      styles.badgeText,
                      item.color ? { color: item.color } : null,
                    ]}
                    weight={FontWeight.bold}
                  >
                    {item.value}
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
    maxHeight: 190,
  },
  scrollContent: {
    paddingVertical: 4,
    paddingHorizontal: 4,
  },
  sectionBlock: {
    width: "100%",
    marginBottom: 6,
  },
  sectionHeader: {
    paddingHorizontal: 8,
    paddingTop: 6,
    paddingBottom: 4,
  },
  sectionTitle: {
    color: "#64748B",
    fontSize: 13.5,
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 7,
    paddingHorizontal: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    backgroundColor: Colors.white,
  },
  itemRowLast: {
    borderBottomColor: "transparent",
  },
  itemLabel: {
    fontSize: 12,
  },
  badge: {
    backgroundColor: Colors.slate100,
    borderRadius: 6,
    minWidth: 26,
    height: 22,
    paddingHorizontal: 7,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    fontSize: 12,
    color: Colors.gray800,
  },
});
