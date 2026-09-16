import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";

import {
  AdminDashboardHeader,
  AssessmentSuitesCard,
  PendingApprovalsCard,
} from "@/components/admin/dashboard";
import AppText from "@/components/ui/AppText";
import { useAdminDashboard } from "@/hooks/useAdminDashboard";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";

export default function AdminDashboardScreen() {
  const router = useRouter();
  const {
    admin,
    pending,
    suites,
    loading,
    refreshing,
    actioningUid,
    error,
    refresh,
    handleApprove,
    handleReject,
    handleLogout,
  } = useAdminDashboard();

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={refresh}
              colors={[Colors.mainColour1]}
              tintColor={Colors.mainColour1}
            />
          }
        >
          <AdminDashboardHeader adminName={admin?.name} onLogout={handleLogout} />

          <View style={styles.body}>
            {error && <AppText style={styles.errorText}>{error}</AppText>}

            <PendingApprovalsCard
              pending={pending}
              loading={loading}
              actioningUid={actioningUid}
              onApprove={handleApprove}
              onReject={handleReject}
            />

            <AssessmentSuitesCard
              suites={suites}
              loading={loading}
              onAddSuite={() => router.push("/assessment_builder")}
              onSelectSuite={(suiteUid) =>
                router.push({ pathname: "/assessment_builder", params: { suiteUid } })
              }
            />
          </View>
        </ScrollView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scrollContent: { flexGrow: 1, paddingBottom: 24 },
  body: { padding: 16, gap: 14 },
  errorText: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    textAlign: "center",
  },
});
