import { ScrollView, StyleSheet, View } from "react-native";

import { TrainingTypeGroup } from "@/api/admin";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type TrainingTypeBreakdownProps = {
  data?: TrainingTypeGroup[];
};

export default function TrainingTypeBreakdown({ data }: TrainingTypeBreakdownProps) {
  // Zero-count rows (and any group left empty by that) are hidden, and with
  // nothing to show the panel renders nothing at all.
  const groups = (data ?? [])
    .map((group) => ({ ...group, statuses: group.statuses.filter((s) => s.count > 0) }))
    .filter((group) => group.statuses.length > 0);

  if (groups.length === 0) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        nestedScrollEnabled
        showsVerticalScrollIndicator
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
      >
        {groups.map((group, gIdx) => (
          <View key={`${group.type}-${gIdx}`} style={styles.groupSection}>
            <View style={styles.groupHeader}>
              <AppText style={styles.groupTitle} weight={FontWeight.bold}>
                {group.type}
              </AppText>
            </View>

            {group.statuses.map((item, sIdx) => (
              <View
                key={`${item.status}-${sIdx}`}
                style={[
                  styles.statusRow,
                  sIdx === group.statuses.length - 1 && styles.statusRowLast,
                ]}
              >
                <AppText style={styles.statusLabel} color={Colors.gray600}>
                  {item.status}
                </AppText>
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
  groupSection: {
    width: "100%",
  },
  groupHeader: {
    backgroundColor: Colors.slate200,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  groupTitle: {
    fontSize: 12,
    color: Colors.gray700,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    backgroundColor: Colors.white,
  },
  statusRowLast: {
    borderBottomColor: Colors.slate200,
  },
  statusLabel: {
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
