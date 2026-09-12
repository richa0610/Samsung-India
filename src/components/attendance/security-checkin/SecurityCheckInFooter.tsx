import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Breakpoints } from "@/theme/breakpoints";
import { FontWeight } from "@/theme/fontWeight";

type SecurityCheckInFooterProps = {
  hasPhoto: boolean;
};

export default function SecurityCheckInFooter({ hasPhoto }: SecurityCheckInFooterProps) {
  if (!hasPhoto) {
    return (
      <View style={styles.blueAlertBanner}>
        <View style={styles.blueShieldIconWrap}>
          <Ionicons name="shield-checkmark" size={18} color="#0066FF" />
        </View>
        <View style={styles.alertTextColumn}>
          <AppText style={styles.alertTitle} weight={FontWeight.semiBold}>
            Make sure your face is clearly visible
          </AppText>
          <AppText style={styles.alertSubtitle}>Good lighting helps verification.</AppText>
        </View>
        <Ionicons name="chevron-forward" size={18} color="#374151" />
      </View>
    );
  }

  return (
    <View style={styles.encryptionFooter}>
      <View style={styles.lockIconCircle}>
        <Ionicons name="lock-closed" size={13} color="#14B8A6" />
      </View>
      <AppText style={styles.encryptionText} weight={FontWeight.medium}>
        Your data is secure and encrypted
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  blueAlertBanner: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    backgroundColor: "#DBEAFE",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 14,
  },
  blueShieldIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "rgba(0, 102, 255, 0.12)",
    alignItems: "center",
    justifyContent: "center",
  },
  alertTextColumn: {
    flex: 1,
    gap: 2,
  },
  alertTitle: {
    fontSize: 11.5,
    color: "#1E293B",
  },
  alertSubtitle: {
    fontSize: 10.5,
    color: "#64748B",
  },
  encryptionFooter: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginTop: 16,
  },
  lockIconCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: "#CCFBF1",
    alignItems: "center",
    justifyContent: "center",
  },
  encryptionText: {
    fontSize: 12,
    color: "#4B5563",
  },
});
