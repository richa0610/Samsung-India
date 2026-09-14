import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontSize, FontWeight } from "@/theme/typography";

export type SubmissionSummaryRow = {
  label: string;
  value: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconColor: string;
  iconBg: string;
};

type SubmissionSummaryCardProps = {
  rows: SubmissionSummaryRow[];
};

export default function SubmissionSummaryCard({ rows }: SubmissionSummaryCardProps) {
  return (
    <View style={styles.summaryCard}>
      <AppText variant="label" weight={FontWeight.semiBold} color="#111827" style={styles.summaryCardTitle}>
        Submission Summary
      </AppText>

      <View style={styles.summaryList}>
        {rows.map((row, index) => (
          <SummaryRow key={row.label} {...row} isLast={index === rows.length - 1} />
        ))}
      </View>
    </View>
  );
}

function SummaryRow({ label, value, icon, iconColor, iconBg, isLast }: SubmissionSummaryRow & { isLast: boolean }) {
  return (
    <View style={[styles.summaryRow, !isLast && styles.summaryRowBorder]}>
      <View style={[styles.summaryIcon, { backgroundColor: iconBg }]}>
        <Ionicons name={icon} size={16} color={iconColor} />
      </View>
      <AppText variant="caption" color="#4B5563" style={styles.summaryLabel}>
        {label}
      </AppText>
      <AppText variant="caption" color="#111827" style={styles.summaryValue}>
        {value}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  summaryCard: {
    width: "100%",
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#F3F4F6",
    paddingHorizontal: 15,
    paddingVertical: 15,
    ...createShadow({ x: 0, y: 2, blur: 6, opacity: 0.04, elevation: 1 }),
  },
  summaryCardTitle: {
    fontSize: 13,
    marginBottom: 6,
  },
  summaryList: {
    gap: 0,
  },
  summaryRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    gap: 10,
  },
  summaryRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  summaryIcon: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    alignItems: "center",
    justifyContent: "center",
  },
  summaryLabel: {
    fontSize: FontSize.tiny,
    flex: 1,
  },
  summaryValue: {
    fontSize: FontSize.tiny,
    textAlign: "right",
  },
});
