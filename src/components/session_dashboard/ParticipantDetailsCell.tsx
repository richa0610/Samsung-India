import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { ParticipantItem } from "./sessionDashboardTypes";

// Short tags for the audience type under the phone number; screen readers get the full word.
const AUDIENCE_DISPLAY: Record<
  ParticipantItem["attendeeType"],
  { label: string; name: string; bg: string; border: string; text: string }
> = {
  ASSIGNED: {
    label: "ASN",
    name: "Assigned",
    bg: Colors.audienceAssignedBg,
    border: Colors.audienceAssignedBorder,
    text: Colors.audienceAssignedText,
  },
  UNASSIGNED: {
    label: "UASN",
    name: "Unassigned",
    bg: Colors.audienceUnassignedBg,
    border: Colors.audienceUnassignedBorder,
    text: Colors.audienceUnassignedText,
  },
  FRESH: {
    label: "FRESH",
    name: "Fresh",
    bg: Colors.audienceFreshBg,
    border: Colors.audienceFreshBorder,
    text: Colors.audienceFreshText,
  },
};

/** The Participant Master List's details cell, one item per line: name, ID, phone, and the
 *  audience tag (ASN / UASN / FRESH) under the phone - there's no audience column of its own. */
export default function ParticipantDetailsCell({ item }: { item: ParticipantItem }) {
  const audience = AUDIENCE_DISPLAY[item.attendeeType];
  return (
    <View style={styles.cell}>
      <AppText style={styles.name} numberOfLines={1}>
        {item.name}
      </AppText>
      <AppText style={styles.empId}>{item.employeeId}</AppText>
      <AppText style={styles.phone} numberOfLines={1}>
        {item.phone}
      </AppText>
      <View
        style={[styles.tag, { backgroundColor: audience.bg, borderColor: audience.border }]}
        accessible
        accessibilityLabel={`Audience: ${audience.name}`}
      >
        <AppText style={[styles.tagText, { color: audience.text }]}>{audience.label}</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // Every line left-aligned, like the column's heading.
  cell: { gap: 1, alignItems: "flex-start" },
  name: { fontSize: 10.5, fontWeight: "700", color: Colors.black, textAlign: "left" },
  empId: { fontSize: 9, color: Colors.brandBlue, fontWeight: "600", textAlign: "left" },
  phone: { fontSize: 9, color: Colors.gray500, textAlign: "left" },
  // Its own line, as wide as its text (not stretched across the column).
  tag: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 3, paddingVertical: 1, marginTop: 1 },
  tagText: { fontSize: 8, fontWeight: "700" },
});
