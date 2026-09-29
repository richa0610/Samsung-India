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
  /** Asks for the next page when the list is scrolled near its end. */
  onLoadMore?: () => void;
  loadingMore?: boolean;
};

// How close to the bottom (px) the list may get before the next page is requested.
const LOAD_MORE_THRESHOLD = 200;

export default function SessionsListContent({
  loading,
  refreshing,
  onRefresh,
  filteredSessions,
  activeTab,
  onLaunch,
  onReport,
  onLoadMore,
  loadingMore = false,
}: SessionsListContentProps) {
  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      scrollEventThrottle={200}
      onScroll={({ nativeEvent: { layoutMeasurement, contentOffset, contentSize } }) => {
        if (layoutMeasurement.height + contentOffset.y >= contentSize.height - LOAD_MORE_THRESHOLD) onLoadMore?.();
      }}
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
          <Ionicons name="calendar-outline" size={48} color={Colors.gray400} />
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
          {loadingMore && <ActivityIndicator style={styles.loadingMore} color={Colors.mainColour1} />}
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
  loadingMore: {
    paddingVertical: 16,
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
    color: Colors.gray500,
    fontWeight: "500",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.gray700,
    marginTop: 8,
  },
  emptySubtitle: {
    fontSize: 12.5,
    color: Colors.gray500,
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 24,
  },
});
