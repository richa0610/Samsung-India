import { ScrollView, StyleSheet, View } from "react-native";

import { AudienceSection } from "@/api/admin";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type AudienceTypeBreakdownProps = {
  data?: AudienceSection[];
};

export default function AudienceTypeBreakdown({ data }: AudienceTypeBreakdownProps) {
  // Zero-count rows (and any section left empty) are hidden; with nothing to
  // show the panel renders nothing at all.
  const sections = (data ?? [])
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
        {sections.map((section, sIdx) => {
          const isCategoryTitle =
            section.title === "Pax Count" || section.title === "Global Totals";

          return (
            <View key={`${section.title}-${sIdx}`} style={styles.sectionBlock}>
              <View style={styles.sectionHeader}>
                <AppText
                  style={[
                    styles.sectionTitle,
                    isCategoryTitle ? styles.categoryTitle : styles.typeTitle,
                  ]}
                  weight={FontWeight.bold}
                >
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
                      {item.count}
                    </AppText>
                  </View>
                </View>
              ))}
            </View>
          );
        })}
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
    fontSize: 13,
  },
  categoryTitle: {
    color: "#64748B",
    fontSize: 13.5,
  },
  typeTitle: {
    color: Colors.gray800,
    fontSize: 13,
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
    minWidth: 24,
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
