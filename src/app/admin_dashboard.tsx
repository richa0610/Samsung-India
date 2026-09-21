import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
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
import { useAdminDashboard } from "@/hooks/useAdminDashboard";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

const ACTIVE_TAB: AdminDashboardTab = "home";

export default function AdminDashboardScreen() {
  const router = useRouter();
  const { admin, pending, stats, refreshing, error, refresh, handleLogout } = useAdminDashboard();
  const [showTrainingTypes, setShowTrainingTypes] = useState(false);
  const [showAudienceTypes, setShowAudienceTypes] = useState(false);
  const [showTrainerStatus, setShowTrainerStatus] = useState(false);
  const [showAssessmentGaps, setShowAssessmentGaps] = useState(false);

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
            onLogout={handleLogout}
          />

          <View style={styles.filterWrap}>
            <AdminFilterBar scope="home" />
          </View>

          {pending.length > 0 && (
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
                <AppText weight={FontWeight.bold} color="#111827" style={styles.alertTitle}>
                  {pending.length} training{pending.length === 1 ? "" : "s"} awaiting review
                </AppText>
                <AppText color="#6B7280" style={styles.alertSub}>
                  Tap to approve, reject or edit
                </AppText>
              </View>
              <Ionicons name="chevron-forward" size={18} color="#B45309" />
            </Pressable>
          )}

          {stats && (
            <AppText variant="tiny" weight={FontWeight.bold} color="#6B7280" style={styles.sectionLabel}>
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
                ringColor="#16A34A"
                ringTrackColor="#7C3AED"
                subItems={[
                  { label: "Completed", value: String(stats.training.completed), color: "#16A34A" },
                  { label: "Pending", value: String(stats.training.pending), color: "#7C3AED" },
                  { label: "Rate", value: `${stats.training.ratePercent}%`, color: "#16A34A" },
                ]}
                linkLabel="View All Types"
                onPressLink={() => setShowTrainingTypes((prev) => !prev)}
                isExpanded={showTrainingTypes}
                expandedContent={<TrainingTypeBreakdown data={stats.training.typeBreakdown} />}
              />
              <AdminStatCard
                title="Audience"
                icon="people"
                accent="#16A34A"
                badgeLabel="Pax"
                bigNumber={stats.audience.participants}
                bigLabel="Participants"
                ringPercentage={stats.audience.presentPercent}
                ringValue={stats.audience.participants}
                ringColor="#16A34A"
                subItems={[
                  {
                    label: "Present",
                    value: `${stats.audience.present} (${stats.audience.presentPercent}%)`,
                    color: "#16A34A",
                  },
                  {
                    label: "Absent",
                    value: `${stats.audience.absent} (${stats.audience.absentPercent}%)`,
                    color: "#DC2626",
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
                ringColor="#0EA5E9"
                subItems={[
                  { label: "In Training", value: String(stats.trainers.inTraining), color: Colors.mainColour1 },
                  { label: "Idle", value: String(stats.trainers.idle), color: "#DC2626" },
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
                accent="#F59E0B"
                badgeLabel="Tests"
                bigNumber={stats.assessment.attempts}
                bigLabel="Attempts"
                ringPercentage={
                  stats.assessment.attempts
                    ? (stats.assessment.passCount / stats.assessment.attempts) * 100
                    : 0
                }
                ringValue={stats.assessment.attempts}
                ringColor="#DC2626"
                subItems={[
                  { label: "Pass", value: String(stats.assessment.passCount), color: "#16A34A" },
                  { label: "Fail", value: String(stats.assessment.failCount), color: "#DC2626" },
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
          pendingCount={pending.length}
          onSelectTab={() => {}}
        />
      </SafeAreaView>
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
    borderColor: "#FDE68A",
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
  errorContainer: { paddingHorizontal: 16, paddingTop: 14 },
  errorText: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    textAlign: "center",
  },
});
