import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";

export default function SecurityBanner() {
  return (
    <View style={styles.securityBanner}>
      <Ionicons name="shield-checkmark-outline" size={24} color="#0066FF" />
      <View style={styles.securityTextColumn}>
        <AppText style={styles.securityTitle} weight={FontWeight.bold}>
          Secure & Verified
        </AppText>
        <AppText style={styles.securitySubtitle}>Your profile information is verified and secure.</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  securityBanner: {
    backgroundColor: "#DCEBFE",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginTop: 2,
  },
  securityTextColumn: { flex: 1, gap: 1 },
  securityTitle: { fontSize: 12, color: "#1E293B" },
  securitySubtitle: { fontSize: 10.5, color: "#64748B" },
});
