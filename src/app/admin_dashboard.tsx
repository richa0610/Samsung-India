import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";

import {
  AdminBottomNav,
  AdminDashboardHeader,
  AdminDashboardTab,
  AdminStatCard,
  AssessmentEligibilityGaps,
  AudienceTypeBreakdown,
  TrainerStatusAnalysis,
  TrainingTypeBreakdown,
} from "@/components/admin/dashboard";
import AdminFilterBar from "@/components/admin/AdminFilterBar";
import AppText from "@/components/ui/AppText";
import LogoutConfirmModal from "@/components/ui/LogoutConfirmModal";
import { useAdminDashboard } from "@/hooks/useAdminDashboard";
import { useAdminPhotoUpload } from "@/hooks/useAdminPhotoUpload";
import { useStaffLogout } from "@/hooks/useStaffLogout";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

const ACTIVE_TAB: AdminDashboardTab = "home";

export default function AdminDashboardScreen() {
  const router = useRouter();
  const { admin, pendingCount, stats, loading, refreshing, error, refresh } = useAdminDashboard();
  const { confirmLogoutOpen, requestLogout, cancelLogout, confirmLogout } = useStaffLogout();
  const { pickAndUpload, uploading } = useAdminPhotoUpload();
  const [showTrainingTypes, setShowTrainingTypes] = useState(false);
  const [showAudienceTypes, setShowAudienceTypes] = useState(false);
  const [showTrainerStatus, setShowTrainerStatus] = useState(false);
  const [showAssessmentGaps, setShowAssessmentGaps] = useState(false);

  // The Audience ring shows Unplanned (Fresh)'s share of participants, not
  // presentPercent - "Global Totals" is the same section View Type Breakdown
  // renders, so this can never disagree with the number shown there.
  const globalAudienceTotals = stats?.audience.typeBreakdown?.find(
    (section) => section.title === "Global Totals",
  );
  const unplannedCount =
    globalAudienceTotals?.items.find((item) => item.label === "Unplanned (Fresh)")?.count ?? 0;
  const unplannedPercent =
    stats && stats.audience.participants > 0
      ? Math.round((unplannedCount / stats.audience.participants) * 100)
      : 0;

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container} edges={["top"]}>
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
          <AdminDashboardHeader
            adminName={admin?.name}
            companyId={admin?.offerId || admin?.username || "OFF26005"}
            avatarUrl={admin?.profilePicture}
            onOpenProfile={pickAndUpload}
            uploadingPhoto={uploading}
            onLogout={requestLogout}
          />

          <View style={styles.filterWrap}>
            <AdminFilterBar scope="home" />
          </View>

          {pendingCount > 0 && (
            <Pressable
              style={styles.alertCard}
              onPress={() => router.push("/admin_pending_trainings")}
              accessibilityRole="button"
              accessibilityLabel="Review pending trainings"
            >
              <View style={styles.alertIcon}>
                <Ionicons name="time" size={20} color="#B45309" />
              </View>
              <View style={styles.alertText}>
                <AppText weight={FontWeight.bold} color={Colors.black} style={styles.alertTitle}>
                  {pendingCount} training{pendingCount === 1 ? "" : "s"} awaiting review
                </AppText>
                <AppText color={Colors.gray500} style={styles.alertSub}>
                  Tap to approve, reject or edit
                </AppText>
              </View>
              <Ionicons name="chevron-forward" size={18} color="#B45309" />
            </Pressable>
          )}

          {loading && !stats && (
            <View style={styles.loadingBlock}>
              <ActivityIndicator color={Colors.mainColour1} />
              <AppText variant="caption" color={Colors.gray600}>Loading dashboard...</AppText>
            </View>
          )}

          {stats && (
            <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray500} style={styles.sectionLabel}>
              OVERVIEW
            </AppText>
          )}

          {stats && (
            <View style={styles.statsColumn}>
              <AdminStatCard
                title="Training"
                icon="calendar"
                accent="#7C3AED"
                badgeLabel="Sessions"
                bigNumber={stats.training.planned}
                bigLabel="Planned"
                ringPercentage={stats.training.ratePercent}
                ringValue={stats.training.planned}
                ringColor={Colors.success}
                ringTrackColor="#7C3AED"
                subItems={[
                  { label: "Completed", value: String(stats.training.completed), color: Colors.success },
                  { label: "Pending", value: String(stats.training.pending), color: "#7C3AED" },
                  { label: "Rate", value: `${stats.training.ratePercent}%`, color: Colors.success },
                ]}
                linkLabel="View All Types"
                onPressLink={() => setShowTrainingTypes((prev) => !prev)}
                isExpanded={showTrainingTypes}
                expandedContent={<TrainingTypeBreakdown data={stats.training.typeBreakdown} />}
              />
              <AdminStatCard
                title="Audience"
                icon="people"
                accent={Colors.success}
                badgeLabel="Pax"
                bigNumber={stats.audience.participants}
                bigLabel="Participants"
                ringPercentage={unplannedPercent}
                ringValue={stats.audience.participants}
                ringColor="#0EA5E9"
                ringTrackColor={Colors.success}
                subItems={[
                  {
                    label: "Present",
                    value: `${stats.audience.present} (${stats.audience.presentPercent}%)`,
                    color: Colors.success,
                  },
                  {
                    label: "Absent",
                    value: `${stats.audience.absent} (${stats.audience.absentPercent}%)`,
                    color: Colors.danger,
                  },
                ]}
                linkLabel="View Type Breakdown"
                onPressLink={() => setShowAudienceTypes((prev) => !prev)}
                isExpanded={showAudienceTypes}
                expandedContent={<AudienceTypeBreakdown data={stats.audience.typeBreakdown} />}
              />
              <AdminStatCard
                title="Trainers"
                icon="ribbon"
                accent="#0EA5E9"
                badgeLabel="Users"
                bigNumber={stats.trainers.pool}
                bigLabel="Pool"
                ringPercentage={stats.trainers.utilizationPercent}
                ringValue={stats.trainers.pool}
                ringColor={Colors.mainColour1}
                ringTrackColor="#68e8de"
                subItems={[
                  { label: "In Training", value: String(stats.trainers.inTraining), color: Colors.mainColour1 },
                  { label: "Idle", value: String(stats.trainers.idle), color: "#68e8de" },
                  { label: "Util.", value: `${stats.trainers.utilizationPercent}%` },
                ]}
                linkLabel="Status Analysis"
                onPressLink={() => setShowTrainerStatus((prev) => !prev)}
                isExpanded={showTrainerStatus}
                expandedContent={<TrainerStatusAnalysis data={stats.trainers.statusAnalysis} />}
              />
              <AdminStatCard
                title="Assessment"
                icon="document-text"
                accent={Colors.warning}
                badgeLabel="Tests"
                bigNumber={stats.assessment.attempts}
                bigLabel="Attempts"
                ringPercentage={
                  stats.assessment.attempts
                    ? (stats.assessment.passCount / stats.assessment.attempts) * 100
                    : 0
                }
                ringValue={stats.assessment.attempts}
                ringColor={Colors.danger}
                subItems={[
                  { label: "Pass", value: String(stats.assessment.passCount), color: Colors.success },
                  { label: "Fail", value: String(stats.assessment.failCount), color: Colors.danger },
                  { label: "Avg", value: `${stats.assessment.avgPercent}%`, color: Colors.mainColour1 },
                ]}
                linkLabel="Eligibility & Gaps"
                onPressLink={() => setShowAssessmentGaps((prev) => !prev)}
                isExpanded={showAssessmentGaps}
                expandedContent={<AssessmentEligibilityGaps data={stats.assessment.eligibilityGaps} />}
              />
            </View>
          )}

          {error && (
            <View style={styles.errorContainer}>
              <AppText style={styles.errorText}>{error}</AppText>
            </View>
          )}
        </ScrollView>

        <AdminBottomNav
          activeTab={ACTIVE_TAB}
          pendingCount={pendingCount}
          onSelectTab={() => {}}
        />
      </SafeAreaView>
      <LogoutConfirmModal visible={confirmLogoutOpen} onCancel={cancelLogout} onConfirm={confirmLogout} />
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scrollContent: { flexGrow: 1, paddingBottom: 24 },
  statsColumn: { gap: 8, paddingHorizontal: 16, paddingTop: 6 },
  filterWrap: { paddingHorizontal: 16, paddingTop: 12 },
  sectionLabel: { letterSpacing: 0.8, paddingHorizontal: 20, paddingTop: 10 },
  alertCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginHorizontal: 16,
    marginTop: 12,
    padding: 12,
    backgroundColor: "#FFFBEB",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#e3b80f",
  },
  alertIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#FEF3C7",
    alignItems: "center",
    justifyContent: "center",
  },
  alertText: { flex: 1, gap: 1 },
  alertTitle: { fontSize: Fonts.bodySm },
  alertSub: { fontSize: Fonts.overline },
  loadingBlock: { alignItems: "center", gap: 8, paddingVertical: 48 },
  errorContainer: { paddingHorizontal: 16, paddingTop: 14 },
  errorText: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    textAlign: "center",
  },
});
