import { Ionicons } from "@expo/vector-icons";
import { Fragment } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { DetailItem } from "./constants";

type DetailsCardProps = {
  tag: string;
  items: DetailItem[];
  onEdit: () => void;
};

export default function DetailsCard({ tag, items, onEdit }: DetailsCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeaderRow}>
        <View style={styles.cardTag}>
          <AppText style={styles.cardTagText} weight={FontWeight.bold}>
            {tag}
          </AppText>
        </View>
        <Pressable style={styles.editButton} onPress={onEdit} accessibilityRole="button" accessibilityLabel={`Edit ${tag.toLowerCase()}`}>
          <Ionicons name="pencil-sharp" size={11} color="#6B7280" />
          <AppText style={styles.editButtonText} weight={FontWeight.semiBold}>
            EDIT
          </AppText>
        </Pressable>
      </View>

      {items.map((item, index) => (
        <Fragment key={item.label}>
          <View style={styles.detailRow}>
            <View style={styles.iconBox}>
              <Ionicons name={item.icon} size={20} color="#0066FF" />
            </View>
            <View style={styles.detailTextColumn}>
              <AppText style={styles.detailLabel}>{item.label}</AppText>
              <AppText style={styles.detailValue} weight={FontWeight.bold}>
                {item.value}
              </AppText>
            </View>
          </View>
          {index < items.length - 1 && <View style={styles.rowDivider} />}
        </Fragment>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 6,
    ...createShadow({ x: 0, y: 4, blur: 14, opacity: 0.06, elevation: 3 }),
  },
  cardHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  cardTag: { backgroundColor: "#E0EFFF", paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  cardTagText: { fontSize: 10.5, color: "#0066FF", letterSpacing: 0.3 },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: Colors.white,
  },
  editButtonText: { fontSize: 10, color: "#6B7280", letterSpacing: 0.2 },
  detailRow: { flexDirection: "row", alignItems: "center", gap: 14, paddingVertical: 10 },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 8,
    backgroundColor: "#E0EFFF",
    alignItems: "center",
    justifyContent: "center",
  },
  detailTextColumn: { flex: 1, gap: 1 },
  detailLabel: { fontSize: 11, color: "#6B7280" },
  detailValue: { fontSize: 14, color: "#111827", letterSpacing: 0.1 },
  rowDivider: { height: 1, backgroundColor: "#F3F4F6" },
});
