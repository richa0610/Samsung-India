import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";

import { RetestModule } from "@/api/session";
import AppButton from "@/components/ui/AppButton";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { formatDisplayDate } from "@/utils/formatDisplayDate";

export type StatusNoticeCardProps = {
  status: "Missed" | "Absent" | "Ongoing" | string;
  title: string;
  message: string;
  sessionTitle?: string;
  date?: string | null;
  location?: string | null;
  trainerName?: string | null;
  onBack: () => void;
  onGoDashboard?: () => void;
  retestItems?: RetestModule[];
  onRetest?: (moduleKey: string, suiteUid: string) => void;
};

export default function StatusNoticeCard({
  status,
  title,
  message,
  sessionTitle,
  date,
  location,
  trainerName,
  onBack,
  onGoDashboard,
  retestItems,
  onRetest,
}: StatusNoticeCardProps) {
  const isMissed = status === "Missed";
  const isAbsent = status === "Absent";
  const isOngoing = status === "Ongoing";
  const isIncomplete = status === "Incomplete";

  const statusColor = isMissed
    ? "#DC2626"
    : isAbsent || isIncomplete
      ? "#D97706"
      : isOngoing
        ? "#2563EB"
        : Colors.blueAccent;

  const statusHaloBg = isMissed
    ? "#FEE2E2"
    : isAbsent || isIncomplete
      ? "#FEF3C7"
      : "#DBEAFE";

  const statusBorderColor = isMissed
    ? "#FCA5A5"
    : isAbsent || isIncomplete
      ? "#FCD34D"
      : "#93C5FD";

  const statusIconName: keyof typeof Ionicons.glyphMap = isMissed
    ? "close"
    : isAbsent || isIncomplete
      ? "alert-circle-outline"
      : "time-outline";

  const badgeText = isMissed
    ? "MISSED SESSION"
    : isAbsent
      ? "MARKED ABSENT"
      : isIncomplete
        ? "INCOMPLETE SESSION"
        : "IN PROGRESS";

  const statusLabel = isMissed
    ? "Missed"
    : isAbsent
      ? "Absent"
      : isIncomplete
        ? "Incomplete"
        : "In Progress";

  const guidanceText = isMissed
    ? "Attendance and verification are required while a training is live. You can review your overall record and upcoming schedules from your dashboard."
    : isAbsent
      ? "You were marked absent for this training. If you believe this was an error, please reach out to your session trainer or coordinator."
      : isIncomplete
        ? "You attended this training, but some required modules were not completed before the session ended."
        : "This training is currently running. All module scores, question breakdowns, and results will appear here once the trainer ends the session.";

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero Outcome Card */}
      <View style={styles.heroCard}>
        <View
          style={[
            styles.badgePill,
            { backgroundColor: statusHaloBg, borderColor: statusBorderColor },
          ]}
        >
          <View style={[styles.badgeDot, { backgroundColor: statusColor }]} />
          <AppText
            variant="tiny"
            weight={FontWeight.bold}
            color={statusColor}
            style={styles.badgeText}
          >
            {badgeText}
          </AppText>
        </View>

        {/* Layered Dual-Ring Halo Icon */}
        <View
          style={[
            styles.haloRing,
            { backgroundColor: statusHaloBg, borderColor: statusBorderColor },
          ]}
        >
          <View style={[styles.solidIconCircle, { backgroundColor: statusColor }]}>
            <Ionicons name={statusIconName} size={30} color={Colors.white} />
          </View>
        </View>

        <AppText
          variant="h2"
          weight={FontWeight.bold}
          color={Colors.black}
          align="center"
          style={styles.heroTitle}
        >
          {title}
        </AppText>

        <AppText
          variant="body"
          color={Colors.gray600}
          align="center"
          style={styles.heroMessage}
        >
          {message}
        </AppText>
      </View>

      {/* Session Details Card */}
      <View style={styles.detailsCard}>
        <View style={styles.cardHeaderRow}>
          <View style={styles.headerIconWrap}>
            <Ionicons name="layers-outline" size={16} color={Colors.headerBlue} />
          </View>
          <AppText variant="label" weight={FontWeight.bold} color={Colors.black} style={styles.cardHeaderText}>
            Session Details
          </AppText>
          <View style={[styles.statusMiniPill, { backgroundColor: statusHaloBg }]}>
            <AppText variant="tiny" weight={FontWeight.bold} color={statusColor}>
              {statusLabel}
            </AppText>
          </View>
        </View>

        <View style={styles.divider} />

        {/* Training Title */}
        <View style={styles.metaRow}>
          <View style={styles.metaIconCol}>
            <Ionicons name="school-outline" size={16} color={Colors.headerBlue} />
          </View>
          <View style={styles.metaTextCol}>
            <AppText variant="tiny" color={Colors.gray400} weight={FontWeight.bold} style={styles.metaLabel}>
              TRAINING
            </AppText>
            <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.black}>
              {sessionTitle || "Training Session"}
            </AppText>
          </View>
        </View>

        {/* Date */}
        <View style={styles.metaRow}>
          <View style={styles.metaIconCol}>
            <Ionicons name="calendar-outline" size={16} color={Colors.headerBlue} />
          </View>
          <View style={styles.metaTextCol}>
            <AppText variant="tiny" color={Colors.gray400} weight={FontWeight.bold} style={styles.metaLabel}>
              SCHEDULED DATE
            </AppText>
            <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.black}>
              {formatDisplayDate(date ?? null)}
            </AppText>
          </View>
        </View>

        {/* Location */}
        {location ? (
          <View style={styles.metaRow}>
            <View style={styles.metaIconCol}>
              <Ionicons name="location-outline" size={16} color={Colors.headerBlue} />
            </View>
            <View style={styles.metaTextCol}>
              <AppText variant="tiny" color={Colors.gray400} weight={FontWeight.bold} style={styles.metaLabel}>
                LOCATION
              </AppText>
              <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.black}>
                {location}
              </AppText>
            </View>
          </View>
        ) : null}

        {/* Trainer */}
        {trainerName ? (
          <View style={styles.metaRow}>
            <View style={styles.metaIconCol}>
              <Ionicons name="person-outline" size={16} color={Colors.headerBlue} />
            </View>
            <View style={styles.metaTextCol}>
              <AppText variant="tiny" color={Colors.gray400} weight={FontWeight.bold} style={styles.metaLabel}>
                TRAINER
              </AppText>
              <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.black}>
                {trainerName}
              </AppText>
            </View>
          </View>
        ) : null}
      </View>

      {/* Available Retests & Survey Card */}
      {retestItems && retestItems.length > 0 && (
        <View style={styles.retestCard}>
          <View style={styles.cardHeaderRow}>
            <View style={[styles.headerIconWrap, { backgroundColor: Colors.blue50 }]}>
              <Ionicons name="refresh-circle-outline" size={17} color={Colors.blueAccent} />
            </View>
            <AppText variant="label" weight={FontWeight.bold} color={Colors.black} style={styles.cardHeaderText}>
              Retest & Survey Retake
            </AppText>
            <View style={[styles.statusMiniPill, { backgroundColor: "#E0F2FE" }]}>
              <AppText variant="tiny" weight={FontWeight.bold} color={Colors.blueAccent}>
                Available
              </AppText>
            </View>
          </View>

          <View style={styles.divider} />

          <AppText variant="tiny" color={Colors.gray500} style={styles.retestDescription}>
            You may take the Post-Test and Survey for this missed session once. Your retest result will be recorded with your profile.
          </AppText>

          <View style={styles.retestList}>
            {retestItems.map((item) => {
              const isStandardTest = item.key === "STANDARD_TEST";
              const iconName: keyof typeof Ionicons.glyphMap = isStandardTest ? "document-text-outline" : "clipboard-outline";

              return (
                <View key={item.key} style={styles.retestItemRow}>
                  <View style={styles.retestItemInfo}>
                    <View style={styles.retestIconWrap}>
                      <Ionicons name={iconName} size={16} color={Colors.blueAccent} />
                    </View>
                    <View style={styles.retestTextCol}>
                      <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.black}>
                        {item.name}
                      </AppText>
                      {item.done && item.score && (
                        <AppText variant="tiny" weight={FontWeight.bold} color={Colors.successTeal}>
                          Score: {item.score}
                        </AppText>
                      )}
                    </View>
                  </View>

                  {item.done ? (
                    <View style={styles.retestDoneBadge}>
                      <Ionicons name="checkmark-done" size={13} color={Colors.successTeal} />
                      <AppText variant="tiny" weight={FontWeight.bold} color={Colors.successTeal}>
                        {item.score ? `Retested (${item.score})` : "Completed"}
                      </AppText>
                    </View>
                  ) : (
                    <Pressable
                      style={styles.retestActionButton}
                      onPress={() => onRetest?.(item.key, item.suiteUid)}
                      accessibilityRole="button"
                      accessibilityLabel={`Start ${item.name}`}
                    >
                      <Ionicons name={isStandardTest ? "reload-outline" : "create-outline"} size={13} color={Colors.white} />
                      <AppText variant="tiny" weight={FontWeight.bold} color={Colors.white}>
                        {isStandardTest ? "Start Retest" : "Take Survey"}
                      </AppText>
                    </Pressable>
                  )}
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Helpful Guidance Notice Card */}
      <View style={styles.guidanceCard}>
        <View style={styles.guidanceHeaderRow}>
          <View style={styles.guidanceIconWrap}>
            <Ionicons name="bulb-outline" size={15} color={Colors.headerBlue} />
          </View>
          <AppText variant="caption" weight={FontWeight.bold} color={Colors.headerBlue}>
            Important Note
          </AppText>
        </View>
        <AppText variant="caption" color={Colors.gray600} style={styles.guidanceText}>
          {guidanceText}
        </AppText>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionWrap}>
        <AppButton
          title="Back to Trainings"
          leftIcon={<Ionicons name="arrow-back" size={16} color={Colors.white} />}
          onPress={onBack}
        />
        {onGoDashboard && (
          <Pressable
            style={styles.secondaryButton}
            onPress={onGoDashboard}
            accessibilityRole="button"
            accessibilityLabel="View Dashboard"
          >
            <Ionicons name="grid-outline" size={15} color={Colors.headerBlue} />
            <AppText variant="bodySmall" weight={FontWeight.semiBold} color={Colors.headerBlue}>
              View Dashboard
            </AppText>
          </Pressable>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    paddingTop: 18,
    paddingBottom: 40,
    gap: 14,
  },
  heroCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    ...Shadows.card,
  },
  badgePill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: Radius.pill,
    borderWidth: 1,
    marginBottom: 16,
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  badgeText: {
    letterSpacing: 0.6,
  },
  haloRing: {
    width: 86,
    height: 86,
    borderRadius: 43,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    marginBottom: 14,
  },
  solidIconCircle: {
    width: 54,
    height: 54,
    borderRadius: 27,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.raised,
  },
  heroTitle: {
    fontSize: 22,
    marginBottom: 6,
    letterSpacing: -0.3,
  },
  heroMessage: {
    lineHeight: 21,
    maxWidth: 320,
  },
  detailsCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    padding: 18,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    ...Shadows.card,
  },
  cardHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  headerIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  cardHeaderText: {
    flex: 1,
  },
  statusMiniPill: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: Radius.pill,
  },
  divider: {
    height: 1,
    backgroundColor: "#F1F5F9",
    marginVertical: 12,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 6,
  },
  metaIconCol: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  metaTextCol: {
    flex: 1,
    gap: 1,
  },
  metaLabel: {
    letterSpacing: 0.5,
  },
  guidanceCard: {
    backgroundColor: "#F0F7FF",
    borderRadius: Radius.lg,
    borderLeftWidth: 4,
    borderLeftColor: Colors.headerBlue,
    padding: 14,
    gap: 6,
  },
  guidanceHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  guidanceIconWrap: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#DCEBFE",
    alignItems: "center",
    justifyContent: "center",
  },
  guidanceText: {
    lineHeight: 18,
  },
  actionWrap: {
    gap: 10,
    marginTop: 4,
  },
  secondaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    borderRadius: Radius.lg,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: "#CBD5E1",
  },
  retestCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    padding: 18,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    ...Shadows.card,
  },
  retestDescription: {
    lineHeight: 18,
    marginBottom: 10,
  },
  retestList: {
    gap: 2,
  },
  retestItemRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.slate100,
    gap: 8,
  },
  retestItemInfo: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    gap: 10,
  },
  retestIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  retestTextCol: {
    flex: 1,
    gap: 1,
  },
  retestDoneBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.successBgSoft,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: Radius.sm,
  },
  retestActionButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: Colors.blueAccent,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: Radius.sm,
  },
});
