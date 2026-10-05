import { ReactNode } from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { Colors } from "@/theme/colors";

export type ProgressRingProps = {
  /** 0-100. Values outside that range are clamped. */
  percentage: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  trackColor?: string;
  /** Rendered centered inside the ring - e.g. a number/label stack. */
  children?: ReactNode;
};

/** Generic circular progress gauge, extracted from the trainee dashboard's
 * Global_Percentage donut so every stat card (admin, trainee, trainer) can
 * share one ring implementation instead of re-deriving the SVG math. */
export default function ProgressRing({
  percentage,
  size = 64,
  strokeWidth = 7,
  color = Colors.brandBlue,
  trackColor = Colors.gray200,
  children,
}: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(100, percentage));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clamped / 100) * circumference;

  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <View style={{ width: size, height: size, transform: [{ rotate: "-90deg" }] }}>
        <Svg width={size} height={size}>
          <Circle cx={size / 2} cy={size / 2} r={radius} stroke={trackColor} strokeWidth={strokeWidth} fill="none" />
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="none"
          />
        </Svg>
      </View>
      {children && (
        <View style={{ position: "absolute", alignItems: "center", justifyContent: "center" }} pointerEvents="none">
          {children}
        </View>
      )}
    </View>
  );
}
