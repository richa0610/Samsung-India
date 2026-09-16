import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import { PendingSessionItem } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

type PendingApprovalRowProps = {
  item: PendingSessionItem;
  isActioning: boolean;
  onApprove: (uid: string) => void;
  onReject: (uid: string) => void;
};

export default function PendingApprovalRow({ item, isActioning, onApprove, onReject }: PendingApprovalRowProps) {
  return (
    <View style={styles.pendingRow}>
      <View style={styles.pendingInfo}>
        <AppText style={styles.pendingTitle} weight={FontWeight.medium}>
          {item.title}
        </AppText>
        <AppText style={styles.pendingMeta} color={Colors.gray600}>
          {item.trainerName ?? "Unknown Trainer"} • {item.conferenceDate ?? "--"} {item.conferenceTime ?? ""}
        </AppText>
      </View>
      {isActioning ? (
        <ActivityIndicator color={Colors.mainColour1} />
      ) : (
        <View style={styles.pendingActions}>
          <Pressable style={styles.rejectButton} onPress={() => onReject(item.conferenceUid)}>
            <Ionicons name="close" size={16} color={Colors.danger} />
          </Pressable>
          <Pressable style={styles.approveButton} onPress={() => onApprove(item.conferenceUid)}>
            <Ionicons name="checkmark" size={16} color={Colors.white} />
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  pendingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: Colors.gray100,
    borderRadius: Radius.xl,
    padding: 12,
  },
  pendingInfo: { flex: 1 },
  pendingTitle: { fontSize: Fonts.bodySm },
  pendingMeta: { fontSize: Fonts.overline, marginTop: 2 },
  pendingActions: { flexDirection: "row", gap: 8 },
  rejectButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.danger,
    alignItems: "center",
    justifyContent: "center",
  },
  approveButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.success,
    alignItems: "center",
    justifyContent: "center",
  },
});
