import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AuthHeader from "@/components/common/AppHeader";
import SecurityFooter from "@/components/common/SecurityFooter";
import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";

import RoleLoginCard from "./RoleLoginCard";
import SocialLoginRow from "./SocialLoginRow";

export default function RoleSelectionScreen() {
  const router = useRouter();

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.content}>
          <AppCard style={styles.card}>
            <AuthHeader />

            <View style={styles.body}>
              <View style={styles.titleSection}>
                <AppText variant="h3" color={Colors.black}>
                  Login as
                </AppText>
                <AppText variant="caption" color={Colors.gray600} style={styles.titleSubtitle}>
                  Choose your role to continue
                </AppText>
                <View style={styles.titleUnderline} />
              </View>

              <RoleLoginCard
                icon="person-outline"
                tone="blue"
                title="Trainer Login"
                subtitle="Create tests, manage trainees and track performance."
                onPress={() => router.push("/trainer_login")}
              />
              <RoleLoginCard
                icon="people-outline"
                tone="green"
                title="Participant Login"
                subtitle="Attempt tests, track progress and improve your skills."
                onPress={() => router.push("/scan")}
              />

              <SocialLoginRow />

              <AppText variant="caption" color={Colors.gray600} align="center" style={styles.contactText}>
                New here? Contact your{" "}
                <AppText variant="caption" color={Colors.mainColour1}>
                  administrator
                </AppText>
              </AppText>
            </View>
          </AppCard>

          <View style={styles.securityFooter}>
            <SecurityFooter />
          </View>
        </ScrollView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#EEF4FF" },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  card: { width: "95%" },
  body: { padding: 20, gap: 12 },
  titleSection: { alignItems: "center", marginBottom: 4 },
  titleSubtitle: { marginTop: 2 },
  titleUnderline: {
    width: 36,
    height: 3,
    borderRadius: Radius.pill,
    backgroundColor: Colors.mainColour1,
    marginTop: 8,
  },
  contactText: { marginTop: 4 },
  securityFooter: { marginTop: 32 },
});
