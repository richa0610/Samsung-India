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
  const groups = data ?? [];

  if (groups.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <AppText style={styles.emptyText} color={Colors.gray600}>
          No training type records found
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
                <AppText style={styles.statusLabel} color="#4B5563">
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
  groupSection: {
    width: "100%",
  },
  groupHeader: {
    backgroundColor: "#E2E8F0",
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  groupTitle: {
    fontSize: 12,
    color: "#374151",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
    backgroundColor: Colors.white,
  },
  statusRowLast: {
    borderBottomColor: "#E2E8F0",
  },
  statusLabel: {
    fontSize: 12,
  },
  badge: {
    backgroundColor: "#F1F5F9",
    borderRadius: 6,
    minWidth: 24,
    height: 22,
    paddingHorizontal: 7,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    fontSize: 12,
    color: "#1F2937",
  },
});
