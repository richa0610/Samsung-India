import React from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Circle, Defs, LinearGradient, Path, Stop } from "react-native-svg";

import AppText from "../AppText";
import { FontWeight } from "@/theme/fontWeight";

type Props = {
  totalMinutes: number;
  remainingMinutes: number;
  remainingSeconds: number;
  size?: number;
  strokeWidth?: number;
};

const TimeProgress = ({
  totalMinutes,
  remainingMinutes,
  remainingSeconds,
  size = 120,
  strokeWidth = 4.8,
}: Props) => {
  const totalSeconds = Math.max(totalMinutes * 60, 1);
  const remaining = Math.max(remainingMinutes * 60 + remainingSeconds, 0);
  const progress = Math.min(Math.max(remaining / totalSeconds, 0), 1);

  const cx = size / 2;
  const cy = size / 2 - 2;
  const radius = 46;

  const startAngle = (140 * Math.PI) / 180;
  const endAngle = (12 * Math.PI) / 180;

  const startX = cx + radius * Math.cos(startAngle);
  const startY = cy + radius * Math.sin(startAngle);
  const endX = cx + radius * Math.cos(endAngle);
  const endY = cy + radius * Math.sin(endAngle);

  // SVG Arc: large-arc-flag = 1 (232deg span), sweep-flag = 1 (clockwise)
  const arcPath = `M ${startX.toFixed(2)} ${startY.toFixed(2)} A ${radius} ${radius} 0 1 1 ${endX.toFixed(2)} ${endY.toFixed(2)}`;

  // Arc length for 232 degrees
  const totalArcLength = radius * ((232 * Math.PI) / 180);
  const dashOffset = totalArcLength * (1 - progress);

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size} style={styles.svg}>
        <Defs>
          <LinearGradient id="timerExactGrad" x1="0%" y1="100%" x2="100%" y2="15%">
            <Stop offset="0%" stopColor="#FF382E" stopOpacity="1" />
            <Stop offset="35%" stopColor="#FF4F4F" stopOpacity="0.95" />
            <Stop offset="65%" stopColor="#FF8585" stopOpacity="0.7" />
            <Stop offset="100%" stopColor="#FFD4D4" stopOpacity="0.2" />
          </LinearGradient>
        </Defs>

        {/* Slender Faint Base Track */}
        <Path
          d={arcPath}
          stroke="#FEE2E2"
          strokeWidth={strokeWidth}
          strokeOpacity={0.3}
          fill="none"
          strokeLinecap="round"
        />

        {/* Slender Dynamic Progress Gradient Arc */}
        <Path
          d={arcPath}
          stroke="url(#timerExactGrad)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={totalArcLength}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
        />
      </Svg>

      <View style={styles.content}>
        {/* Compact Clock Icon */}
        <View style={styles.clockIconWrapper}>
          <Svg width={17} height={17} viewBox="0 0 17 17">
            <Circle
              cx={8.5}
              cy={8.5}
              r={7}
              fill="#FF7F7F"
              stroke="#111827"
              strokeWidth={1.4}
            />
            {/* 12 o'clock minute hand */}
            <Path
              d="M 8.5 8.5 L 8.5 4.5"
              stroke="#111827"
              strokeWidth={1.4}
              strokeLinecap="round"
            />
            {/* 4 o'clock hour hand */}
            <Path
              d="M 8.5 8.5 L 11.2 10.2"
              stroke="#111827"
              strokeWidth={1.4}
              strokeLinecap="round"
            />
            {/* Center Pin */}
            <Circle cx={8.5} cy={8.5} r={0.8} fill="#111827" />
          </Svg>
        </View>

        {/* Bold Time Text */}
        <AppText style={styles.time} weight={FontWeight.bold}>
          {String(remainingMinutes).padStart(2, "0")}:
          {String(remainingSeconds).padStart(2, "0")}
        </AppText>

        {/* Time Left Label */}
        <AppText style={styles.label} weight={FontWeight.semiBold}>
          Time Left
        </AppText>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  svg: {
    position: "absolute",
    top: 0,
    left: 0,
  },
  content: {
    alignItems: "center",
    justifyContent: "center",
  },
  clockIconWrapper: {
    width: 17,
    height: 17,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  time: {
    fontSize: 17.5,
    lineHeight: 21,
    color: "#000000",
    letterSpacing: 0.2,
  },
  label: {
    marginTop: 1,
    fontSize: 10.5,
    lineHeight: 12.5,
    color: "#FF3328",
  },
});

export default TimeProgress;
