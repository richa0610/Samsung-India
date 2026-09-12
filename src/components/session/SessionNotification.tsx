import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

export type SessionNotificationProps = {
  title?: string;
  message?: string;
  onPress?: () => void;
};

export default function SessionNotification({
  title = "Stay Updated",
  message = "We'll notify you when the next session is ready .",
  onPress,
}: SessionNotificationProps) {
  const ContainerComponent = onPress ? Pressable : View;

  return (
    <ContainerComponent
      style={styles.container}
      onPress={onPress}
      accessibilityRole={onPress ? "button" : undefined}
      accessibilityLabel={title}
    >
      {/* Circular Bell Icon */}
      <View style={styles.iconContainer}>
        <Ionicons
          name="notifications"
          size={19}
          color={Colors.headerBlue}
        />
      </View>

      {/* Text Copy */}
      <View style={styles.textWrap}>
        <AppText
          variant="label"
          color={Colors.black}
          weight={FontWeight.bold}
        >
          {title}
        </AppText>
        <AppText
          variant="caption"
          color={Colors.gray600}
          weight={FontWeight.medium}
        >
          {message}
        </AppText>
      </View>

      {/* Right Chevron */}
      <Ionicons
        name="chevron-forward"
        size={20}
        color={Colors.headerBlue}
      />
    </ContainerComponent>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.notificationBg,
    borderRadius: 14,
    padding: 14,
    gap: 12,
  },
  iconContainer: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.notificationIconBg,
    justifyContent: "center",
    alignItems: "center",
  },
  textWrap: {
    flex: 1,
    gap: 2,
  },
});
