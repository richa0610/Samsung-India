import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { ConnectionIndicator, HeaderActionsPill } from "./quiz-live-header";

export type QuizLiveHeaderProps = {
  onSync?: () => void;
  onRefresh?: () => void;
  isConnected?: boolean;
  isSyncing?: boolean;
  isRefreshing?: boolean;
  showConnectionLabel?: boolean;
};

export default function QuizLiveHeader({
  onSync,
  onRefresh,
  isConnected = true,
  isSyncing = false,
  isRefreshing = false,
  showConnectionLabel = false,
}: QuizLiveHeaderProps) {
  return (
    <View style={styles.header}>
      <View style={styles.titleSection}>
        <Ionicons name="flash" size={16} color="#FACC15" />
        <AppText style={styles.titleText} color={Colors.white} weight={FontWeight.bold} numberOfLines={1}>
          LIVE QUIZ
        </AppText>
      </View>

      <View style={styles.actions}>
        <HeaderActionsPill onSync={onSync} onRefresh={onRefresh} isSyncing={isSyncing} isRefreshing={isRefreshing} />
        <ConnectionIndicator isConnected={isConnected} showConnectionLabel={showConnectionLabel} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    height: 44,
    marginHorizontal: 14,
    marginTop: 6,
    borderRadius: 12,
    backgroundColor: Colors.headerBlue,
    paddingHorizontal: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  titleSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    flexShrink: 0,
  },
  titleText: {
    fontSize: 15,
    letterSpacing: 0.2,
  },
  actions: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    flexShrink: 1,
  },
});
