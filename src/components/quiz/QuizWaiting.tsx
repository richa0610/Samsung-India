import { Ionicons } from "@expo/vector-icons";
import React, { useEffect, useMemo } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import Bell from "@/assets/images/svg/bell.svg";
import Clock from "@/assets/images/svg/clock.svg";
import Eye from "@/assets/images/svg/eye.svg";
import People from "@/assets/images/svg/people.svg";
import Refresh from "@/assets/images/svg/Refresh cw.svg";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export const QUIZ_WAITING_ICON_SIZE = 26;
export const QUIZ_WAITING_CONTAINER_SIZE = 49;

export type QuizWaitingProps = {
  onSyncNow?: () => void;
  message?: string;
  nextQuestionNumber?: number;
};

export default function QuizWaiting({
  onSyncNow,
  message = "Look at the main screen.\nThe quiz will begin shortly!",
  nextQuestionNumber,
}: QuizWaitingProps) {
  const progressPosition = useMemo(() => new Animated.Value(0), []);

  useEffect(() => {
    const progressAnimation = Animated.loop(
      Animated.timing(progressPosition, {
        toValue: 1,
        duration: 1150,
        easing: Easing.inOut(Easing.cubic),
        useNativeDriver: Platform.OS !== "web",
      }),
    );

    progressAnimation.start();
    return () => progressAnimation.stop();
  }, [progressPosition]);

  const progressTranslateX = useMemo(
    () =>
      progressPosition.interpolate({
        inputRange: [0, 1],
        outputRange: [-28, 28],
      }),
    [progressPosition],
  );

  return (
    <View style={styles.content}>
      {/* Upper/Center Hero Section */}
      <View style={styles.heroSection}>
        <View style={styles.trainerIcon}>
          <People width={105} height={88} />
        </View>

        <View style={styles.titleWrapper}>
          <AppText style={styles.title} weight={FontWeight.semiBold}>
            Waiting for
          </AppText>
          <AppText
            style={styles.title}
            color={Colors.headerBlue}
            weight={FontWeight.semiBold}
          >
            Trainer...
          </AppText>
        </View>

        <View
          style={styles.progress}
          accessibilityRole="progressbar"
          accessibilityLabel="Waiting for trainer"
        >
          <Animated.View
            style={[
              styles.progressFill,
              { transform: [{ translateX: progressTranslateX }] },
            ]}
          />
        </View>

        <AppText style={styles.message} weight={FontWeight.medium}>
          {message}
        </AppText>
      </View>

      {/* Bottom Cards Section */}
      <View style={styles.bottomSection}>
        <View style={styles.infoCard}>
          <InfoItem
            icon={
              <Clock
                width={QUIZ_WAITING_ICON_SIZE}
                height={QUIZ_WAITING_ICON_SIZE}
                style={styles.statusSvgIcon}
              />
            }
            title="Stay Ready"
            text={
              nextQuestionNumber
                ? `Question ${nextQuestionNumber} starting soon`
                : "The quiz will start automatically"
            }
            color="#DDEEFF"
          />
          <InfoItem
            icon={
              <Eye
                width={QUIZ_WAITING_ICON_SIZE}
                height={QUIZ_WAITING_ICON_SIZE}
                style={styles.statusSvgIcon}
              />
            }
            title="Stay Focused"
            text="Keep your eyes on the main screen"
            color="#D8F8EB"
          />
          <InfoItem
            icon={
              <Bell
                width={QUIZ_WAITING_ICON_SIZE}
                height={QUIZ_WAITING_ICON_SIZE}
                style={styles.statusSvgIcon}
              />
            }
            title="Stay Connected"
            text="Do not refresh or leave the page"
            color="#FFF2C7"
          />
        </View>

        {onSyncNow && (
          <Pressable
            style={styles.syncNotice}
            onPress={onSyncNow}
            accessibilityRole="button"
            accessibilityLabel="Sync Live Now"
          >
            <View style={styles.syncIcon}>
              <Refresh width={17} height={17} />
            </View>
            <View style={styles.syncCopy}>
              <AppText style={styles.syncTitle} weight={FontWeight.bold}>
                Sync Live Now
              </AppText>
              <AppText style={styles.syncText}>
                Click to re-sync with the live session
              </AppText>
            </View>
            <Ionicons
              name="chevron-forward"
              size={18}
              color={Colors.headerBlue}
            />
          </Pressable>
        )}
      </View>
    </View>
  );
}

export function InfoItem({
  icon,
  title,
  text,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
  color: string;
}) {
  return (
    <View style={styles.infoItem}>
      <View style={[styles.infoIcon, { backgroundColor: color }]}>
        <View style={styles.iconWrapper}>{icon}</View>
      </View>
      <AppText style={styles.infoTitle} weight={FontWeight.medium}>
        {title}
      </AppText>
      <AppText style={styles.infoText} weight={FontWeight.medium}>
        {text}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    flex: 1,
    width: "100%",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
  },
  heroSection: {
    flex: 1,
    width: "100%",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: 10,
    paddingBottom: 50,
  },
  trainerIcon: {
    width: 172,
    height: 172,
    borderRadius: 86,
    borderWidth: 2.5,
    borderColor: Colors.headerBlue,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.08, elevation: 3 }),
  },
  titleWrapper: {
    alignItems: "center",
  },
  title: {
    fontSize: 30,
    lineHeight: 36,
  },
  progress: {
    width: 44,
    height: 3,
    borderRadius: 2,
    overflow: "hidden",
    backgroundColor: Colors.gray200,
  },
  progressFill: {
    width: 22,
    height: "100%",
    borderRadius: 2,
    backgroundColor: Colors.headerBlue,
  },
  message: {
    fontSize: 13,
    textAlign: "center",
    lineHeight: 19,
    color: Colors.gray600,
    paddingHorizontal: 16,
  },
  bottomSection: {
    width: "100%",
    gap: 12,
    paddingTop: 8,
  },
  infoCard: {
    width: "100%",
    minHeight: 160,
    alignItems: "center",
    backgroundColor: Colors.white,
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 2, blur: 8, opacity: 0.06, elevation: 2 }),
  },
  infoItem: {
    width: "31%",
    alignItems: "center",
  },
  infoIcon: {
    width: QUIZ_WAITING_CONTAINER_SIZE,
    height: QUIZ_WAITING_CONTAINER_SIZE,
    borderRadius: QUIZ_WAITING_CONTAINER_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  iconWrapper: {
    width: QUIZ_WAITING_ICON_SIZE,
    height: QUIZ_WAITING_ICON_SIZE,
    alignItems: "center",
    justifyContent: "center",
  },
  statusSvgIcon: {
    width: QUIZ_WAITING_ICON_SIZE,
    height: QUIZ_WAITING_ICON_SIZE,
  },
  infoTitle: {
    fontSize: 11,
    marginTop: 8,
  },
  infoText: {
    fontSize: 9.5,
    color: Colors.gray600,
    textAlign: "center",
    lineHeight: 13,
    marginTop: 4,
  },
  syncNotice: {
    width: "100%",
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: "#DDEEFF",
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  syncIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#CBE5FF",
    alignItems: "center",
    justifyContent: "center",
  },
  syncCopy: {
    flex: 1,
  },
  syncTitle: {
    fontSize: 13,
    color: Colors.black,
  },
  syncText: {
    fontSize: 11,
    color: Colors.gray600,
    marginTop: 1,
  },
});
