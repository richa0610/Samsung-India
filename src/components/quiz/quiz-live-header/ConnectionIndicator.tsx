import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type ConnectionIndicatorProps = {
  isConnected: boolean;
  showConnectionLabel: boolean;
};

export default function ConnectionIndicator({ isConnected, showConnectionLabel }: ConnectionIndicatorProps) {
  const backgroundColor = isConnected ? Colors.statusGreen : Colors.gray400;

  if (showConnectionLabel) {
    return (
      <View style={[styles.connectionPill, { backgroundColor }]}>
        <Ionicons name="wifi" size={12} color={Colors.white} />
        <AppText style={styles.connectionPillText} color={Colors.white} weight={FontWeight.bold} numberOfLines={1}>
          {isConnected ? "CONNECTED" : "OFFLINE"}
        </AppText>
      </View>
    );
  }

  return (
    <View style={[styles.wifiBadge, { backgroundColor }]}>
      <Ionicons name="wifi" size={13} color={Colors.white} />
    </View>
  );
}

const styles = StyleSheet.create({
  wifiBadge: {
    width: 24,
    height: 24,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  connectionPill: {
    height: 24,
    borderRadius: 6,
    paddingHorizontal: 7,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  connectionPillText: {
    fontSize: 9,
    letterSpacing: 0.1,
  },
});
