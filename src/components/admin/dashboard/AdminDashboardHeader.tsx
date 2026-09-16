import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

type AdminDashboardHeaderProps = {
  adminName?: string;
  onLogout: () => void;
};

export default function AdminDashboardHeader({ adminName, onLogout }: AdminDashboardHeaderProps) {
  return (
    <View style={styles.banner}>
      <View style={styles.topBar}>
        <View>
          <AppText style={styles.welcome} color={Colors.white}>
            Welcome back,
          </AppText>
          <AppText style={styles.welcomeName} color={Colors.white} weight={FontWeight.bold}>
            {adminName ?? "Admin"}
          </AppText>
        </View>
        <Pressable style={styles.logoutButton} onPress={onLogout}>
          <Ionicons name="power" size={20} color={Colors.mainColour1} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: Colors.mainColour1,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 24,
    borderBottomLeftRadius: Radius.xxxl,
    borderBottomRightRadius: Radius.xxxl,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  welcome: { fontSize: Fonts.bodySm, opacity: 0.85 },
  welcomeName: { fontSize: Fonts.h2, marginTop: 2 },
  logoutButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
});
