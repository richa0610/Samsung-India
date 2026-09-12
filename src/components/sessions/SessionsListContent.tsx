import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { TrainingAgendaItem } from "@/api/training";
import { Colors } from "@/theme/colors";
import SessionCard from "./SessionCard";
import { SessionTab } from "./sessionsUtils";

type SessionsListContentProps = {
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  filteredSessions: TrainingAgendaItem[];
  activeTab: SessionTab;
  onLaunch: (conferenceUid: string) => void;
  onReport: (conferenceUid: string) => void;
};

export default function SessionsListContent({
  loading,
  refreshing,
  onRefresh,
  filteredSessions,
  activeTab,
  onLaunch,
  onReport,
}: SessionsListContentProps) {
  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />
      }
    >
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.mainColour1} />
          <AppText style={styles.loadingText}>Loading sessions...</AppText>
        </View>
      ) : filteredSessions.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="calendar-outline" size={48} color="#9CA3AF" />
          <AppText style={styles.emptyTitle}>No Sessions Found</AppText>
          <AppText style={styles.emptySubtitle}>
            {activeTab === "completed"
              ? "No completed sessions for this period."
              : activeTab === "today"
                ? "No sessions scheduled for today."
                : "No sessions match your search criteria."}
          </AppText>
        </View>
      ) : (
        <View style={styles.list}>
          {filteredSessions.map((session) => (
            <SessionCard key={session.conferenceUid} item={session} onLaunch={onLaunch} onReport={onReport} />
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 24,
    flexGrow: 1,
  },
  list: {
    gap: 4,
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 60,
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    color: "#6B7280",
    fontWeight: "500",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#374151",
    marginTop: 8,
  },
  emptySubtitle: {
    fontSize: 12.5,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 24,
  },
});
