import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type HeaderActionsPillProps = {
  onSync?: () => void;
  onRefresh?: () => void;
  isSyncing: boolean;
  isRefreshing: boolean;
};

export default function HeaderActionsPill({ onSync, onRefresh, isSyncing, isRefreshing }: HeaderActionsPillProps) {
  if (!onSync && !onRefresh) return null;

  return (
    <View style={styles.actionsPill}>
      {onSync && (
        <Pressable style={styles.actionItem} onPress={onSync} accessibilityRole="button" accessibilityLabel="Sync live quiz">
          <Ionicons name="sync" size={11} color={Colors.headerBlue} style={isSyncing ? styles.spinningIcon : undefined} />
          <AppText style={styles.actionItemText} color={Colors.headerBlue} weight={FontWeight.bold} numberOfLines={1}>
            SYNC LIVE QUIZ
          </AppText>
        </Pressable>
      )}

      {onSync && onRefresh && <View style={styles.divider} />}

      {onRefresh && (
        <Pressable style={styles.actionItem} onPress={onRefresh} accessibilityRole="button" accessibilityLabel="Refresh">
          <Ionicons name="sync" size={11} color={Colors.headerBlue} style={isRefreshing ? styles.spinningIcon : undefined} />
          <AppText style={styles.actionItemText} color={Colors.headerBlue} weight={FontWeight.bold} numberOfLines={1}>
            REFRESH
          </AppText>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  actionsPill: {
    height: 24,
    borderRadius: 6,
    backgroundColor: Colors.white,
    flexDirection: "row",
    alignItems: "center",
  },
  actionItem: {
    height: "100%",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
    paddingHorizontal: 6,
  },
  actionItemText: {
    fontSize: 9,
    letterSpacing: 0.1,
  },
  divider: {
    width: 1,
    alignSelf: "stretch",
    marginVertical: 5,
    backgroundColor: "#CBD5E1",
  },
  spinningIcon: {
    transform: [{ rotate: "180deg" }],
  },
});
