import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";

/** Decorative only — no OAuth provider is wired up in this mock-data app. */
export default function SocialLoginRow() {
  return (
    <View>
      <View style={styles.dividerRow}>
        <View style={styles.dividerLine} />
        <AppText variant="overline" color={Colors.gray400}>
          Or continue with
        </AppText>
        <View style={styles.dividerLine} />
      </View>
      <View style={styles.buttonsRow}>
        <Pressable style={styles.socialButton}>
          <Ionicons name="logo-google" size={16} color="#EA4335" />
          <AppText variant="caption" color={Colors.gray600}>
            Google
          </AppText>
        </Pressable>
        <Pressable style={styles.socialButton}>
          <Ionicons name="logo-microsoft" size={16} color="#00A4EF" />
          <AppText variant="caption" color={Colors.gray600}>
            Microsoft
          </AppText>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  dividerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginVertical: 16,
  },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.gray200 },
  buttonsRow: { flexDirection: "row", gap: 10 },
  socialButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    height: 44,
    borderRadius: Radius.xl,
    borderWidth: 1,
    borderColor: Colors.gray200,
    backgroundColor: Colors.white,
  },
});
