import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type Props = {
  label: string;
  live?: boolean;
  liveColor?: string;
  completed?: boolean;
  missed?: boolean;
  scoreBadge?: boolean;
  locked?: boolean;
};

export default function SessionStatusBadge({
  label,
  live = false,
  liveColor,
  completed = false,
  missed = false,
  scoreBadge = false,
  locked = false,
}: Props) {
  const isUpcoming = !live && !completed && !missed && !scoreBadge && !locked;

  return (
    <View
      style={[
        styles.container,
        live && [styles.liveContainer, liveColor ? { backgroundColor: liveColor } : undefined],
        completed && styles.completedContainer,
        scoreBadge && styles.scoreBadgeContainer,
        missed && styles.missedContainer,
        locked && styles.lockedContainer,
        isUpcoming && styles.upcomingContainer,
      ]}
    >
      {scoreBadge ? (
        <Ionicons name="star" size={11} color={Colors.white} />
      ) : completed ? (
        <Ionicons name="checkmark" size={11} color={Colors.white} />
      ) : live ? (
        <View style={styles.liveDot} />
      ) : missed ? (
        <Ionicons name="close-circle" size={11} color={Colors.danger} />
      ) : locked ? (
        <Ionicons name="lock-closed" size={11} color={Colors.white} />
      ) : null}

      <AppText
        style={[
          styles.text,
          (live || scoreBadge) && styles.liveText,
          completed && styles.completedText,
          missed && styles.missedText,
          locked && styles.lockedText,
          isUpcoming && styles.upcomingText,
        ]}
        weight={FontWeight.bold}
      >
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderRadius: 5,
    paddingHorizontal: 8,
    paddingVertical: 3.5,
  },
  liveContainer: {
    backgroundColor: Colors.headerBlue,
  },
  scoreBadgeContainer: {
    backgroundColor: Colors.headerBlue,
  },
  completedContainer: {
    backgroundColor: Colors.recordedGreen,
  },
  missedContainer: {
    backgroundColor: "#FEE2E2",
  },
  upcomingContainer: {
    borderWidth: 1.2,
    borderColor: Colors.headerBlue,
    backgroundColor: "transparent",
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.white,
  },
  text: {
    fontSize: 9.5,
    letterSpacing: 0.2,
  },

  liveText: {
    color: Colors.white,
  },
  completedText: {
    color: Colors.white,
  },
  missedText: {
    color: Colors.danger,
  },
  upcomingText: {
    color: Colors.headerBlue,
  },
  lockedContainer: {
    backgroundColor: "#EF4444",
  },
  lockedText: {
    color: Colors.white,
  },
});
