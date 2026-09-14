import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import PersonCheckIcon from "@/assets/images/svg/session/person_check.svg";
import PersonAddDisabledIcon from "@/assets/images/svg/session/person_add_disabled.svg";
import PersonCancelIcon from "@/assets/images/svg/session/person_cancel.svg";
import AssignmentIcon from "@/assets/images/svg/session/assignment.svg";
import PersonRemoveIcon from "@/assets/images/svg/session/person_remove.svg";
import AddNotesIcon from "@/assets/images/svg/session/add_notes.svg";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type AudienceBreakdownCardProps = {
  totalAudience?: number;
  present?: number;
  notMarked?: number;
  absent?: number;
  assigned?: number;
  unassigned?: number;
  fresh?: number;
  hasStarted?: boolean;
};

export default function AudienceBreakdownCard({
  totalAudience: totalAudienceProp = 0,
  present: presentProp = 0,
  notMarked: notMarkedProp = 0,
  absent: absentProp = 0,
  assigned: assignedProp = 0,
  unassigned: unassignedProp = 0,
  fresh: freshProp = 0,
  hasStarted = true,
}: AudienceBreakdownCardProps) {
  const totalAudience = hasStarted ? totalAudienceProp : 0;
  const present = hasStarted ? presentProp : 0;
  const notMarked = hasStarted ? notMarkedProp : 0;
  const absent = hasStarted ? absentProp : 0;
  const assigned = hasStarted ? assignedProp : 0;
  const unassigned = hasStarted ? unassignedProp : 0;
  const fresh = hasStarted ? freshProp : 0;

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerIconBox}>
          <Ionicons name="people" size={18} color="#0066FF" />
        </View>
        <AppText style={styles.title}>AUDIENCE BREAKDOWN</AppText>
      </View>

      {/* Total Audience Box */}
      <View style={styles.totalBox}>
        <AppText style={styles.totalLabel}>TOTAL AUDIENCE</AppText>
        <AppText style={styles.totalValue}>{totalAudience}</AppText>
      </View>

      {/* 2x3 Metric Cards Grid */}
      <View style={styles.grid}>
        {/* Card 1: PRESENT */}
        <View style={[styles.metricCard, styles.presentCard]}>
          <View style={[styles.iconBox, styles.presentIconBox]}>
            <PersonCheckIcon width={18} height={14} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText style={[styles.metricLabel, { color: "#10B981" }]}>
              PRESENT
            </AppText>
            <AppText style={styles.metricValue}>{present}</AppText>
          </View>
        </View>

        {/* Card 2: NOT MARKED */}
        <View style={[styles.metricCard, styles.notMarkedCard]}>
          <View style={[styles.iconBox, styles.notMarkedIconBox]}>
            <PersonAddDisabledIcon width={18} height={18} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText
              style={[styles.metricLabel, { color: "#EAB308" }]}
              numberOfLines={1}
            >
              NOT MARKED
            </AppText>
            <AppText style={styles.metricValue}>{notMarked}</AppText>
          </View>
        </View>

        {/* Card 3: ABSENT */}
        <View style={[styles.metricCard, styles.absentCard]}>
          <View style={[styles.iconBox, styles.absentIconBox]}>
            <PersonCancelIcon width={18} height={14} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText style={[styles.metricLabel, { color: "#EF4444" }]}>
              ABSENT
            </AppText>
            <AppText style={styles.metricValue}>{absent}</AppText>
          </View>
        </View>

        {/* Card 4: ASSIGNED */}
        <View style={[styles.metricCard, styles.neutralCard]}>
          <View style={[styles.iconBox, styles.neutralIconBox]}>
            <AssignmentIcon width={16} height={18} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText style={[styles.metricLabel, { color: "#6B7280" }]}>
              ASSIGNED
            </AppText>
            <AppText style={styles.metricValue}>{assigned}</AppText>
          </View>
        </View>

        {/* Card 5: UNASSIGNED */}
        <View style={[styles.metricCard, styles.neutralCard]}>
          <View style={[styles.iconBox, styles.neutralIconBox]}>
            <PersonRemoveIcon width={18} height={14} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText
              style={[styles.metricLabel, { color: "#6B7280" }]}
              numberOfLines={1}
            >
              UNASSIGNED
            </AppText>
            <AppText style={styles.metricValue}>{unassigned}</AppText>
          </View>
        </View>

        {/* Card 6: FRESH */}
        <View style={[styles.metricCard, styles.neutralCard]}>
          <View style={[styles.iconBox, styles.neutralIconBox]}>
            <AddNotesIcon width={16} height={16} />
          </View>
          <View style={styles.metricTextCol}>
            <AppText style={[styles.metricLabel, { color: "#6B7280" }]}>
              FRESH
            </AppText>
            <AppText style={styles.metricValue}>{fresh}</AppText>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  headerIconBox: {
    width: 28,
    height: 28,
    borderWidth: 1.8,
    borderColor: "#0066FF",
    borderRadius: 4,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#111827",
    letterSpacing: 0.3,
  },
  totalBox: {
    backgroundColor: "#F0F6FF",
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: "#60A5FA",
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },
  totalLabel: {
    fontSize: 11,
    fontWeight: "800",
    color: "#0066FF",
    letterSpacing: 0.5,
  },
  totalValue: {
    fontSize: 26,
    fontWeight: "800",
    color: "#111827",
    marginTop: 2,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    justifyContent: "space-between",
  },
  metricCard: {
    width: "31.5%",
    borderRadius: 12,
    borderWidth: 1.2,
    paddingVertical: 8,
    paddingHorizontal: 5,
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  presentCard: {
    backgroundColor: "#F0FDF4",
    borderColor: "#10B981",
  },
  notMarkedCard: {
    backgroundColor: "#FEFCE8",
    borderColor: "#FACC15",
  },
  absentCard: {
    backgroundColor: "#FEF2F2",
    borderColor: "#F87171",
  },
  neutralCard: {
    backgroundColor: Colors.gray50,
    borderColor: "#E5E7EB",
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  presentIconBox: {
    backgroundColor: "#DCFCE7",
  },
  notMarkedIconBox: {
    backgroundColor: "#FEF9C3",
  },
  absentIconBox: {
    backgroundColor: "#FEE2E2",
  },
  neutralIconBox: {
    backgroundColor: "#F3F4F6",
  },
  metricTextCol: {
    flex: 1,
    justifyContent: "center",
  },
  metricLabel: {
    fontSize: 7.5,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  metricValue: {
    fontSize: 15,
    fontWeight: "800",
    color: "#111827",
    marginTop: 1,
  },
});
