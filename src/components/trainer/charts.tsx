import { View, StyleSheet } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type DonutSegment = {
  label: string;
  value: number;
  color: string;
};

type DonutChartProps = {
  segments: DonutSegment[];
  centerValue: string;
  centerLabel: string;
  size?: number;
};

export function DonutChart({ segments, centerValue, centerLabel, size = 132 }: DonutChartProps) {
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const total = segments.reduce((sum, segment) => sum + segment.value, 0) || 1;
  const gap = 3;

  const arcs: (DonutSegment & { length: number; offset: number })[] = [];
  let currentOffset = 0;
  for (const segment of segments) {
    const length = Math.max((segment.value / total) * circumference - gap, 0);
    arcs.push({ ...segment, length, offset: currentOffset });
    currentOffset += (segment.value / total) * circumference;
  }

  return (
    <View style={styles.donutWrap}>
      <View style={{ width: size, height: size, transform: [{ rotate: "-90deg" }] }}>
        <Svg width={size} height={size}>
          <Circle cx={size / 2} cy={size / 2} r={radius} stroke={Colors.gray100} strokeWidth={strokeWidth} fill="none" />
          {arcs.map((arc) => (
            <Circle
              key={arc.label}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={arc.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${arc.length} ${circumference}`}
              strokeDashoffset={-arc.offset}
              fill="none"
            />
          ))}
        </Svg>
      </View>
      <View style={styles.donutCenter} pointerEvents="none">
        <AppText style={styles.donutValue} weight={FontWeight.bold}>{centerValue}</AppText>
        <AppText style={styles.donutLabel} color={Colors.gray600}>{centerLabel}</AppText>
      </View>
    </View>
  );
}

type GaugeSegment = {
  label: string;
  value: number;
  color: string;
};

type GaugeChartProps = {
  segments: GaugeSegment[];
  centerValue: string;
  centerLabel: string;
  size?: number;
};

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  // 0deg = top, sweeping clockwise - matches how the gauge's -90..90 range reads visually.
  const angleRad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const clampedEnd = endAngle - startAngle >= 180 ? startAngle + 179.99 : endAngle;
  const start = polarToCartesian(cx, cy, r, startAngle);
  const end = polarToCartesian(cx, cy, r, clampedEnd);
  return `M ${start.x} ${start.y} A ${r} ${r} 0 0 1 ${end.x} ${end.y}`;
}

const GAUGE_START = -90;
const GAUGE_END = 90;
const GAUGE_SPAN = GAUGE_END - GAUGE_START;

export function GaugeChart({ segments, centerValue, centerLabel, size = 160 }: GaugeChartProps) {
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const height = size / 2 + strokeWidth;
  const total = segments.reduce((sum, segment) => sum + segment.value, 0) || 1;
  const gap = 2;

  const arcs: (GaugeSegment & { start: number; end: number })[] = [];
  let currentAngle = GAUGE_START;
  for (const segment of segments) {
    const span = Math.max((segment.value / total) * GAUGE_SPAN - gap, 0);
    arcs.push({ ...segment, start: currentAngle, end: currentAngle + span });
    currentAngle += (segment.value / total) * GAUGE_SPAN;
  }

  return (
    <View style={[styles.donutWrap, { height }]}>
      <Svg width={size} height={height}>
        <Path
          d={describeArc(cx, cy, radius, GAUGE_START, GAUGE_END)}
          stroke={Colors.gray100}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
        />
        {arcs.map((arc) => (
          <Path
            key={arc.label}
            d={describeArc(cx, cy, radius, arc.start, arc.end)}
            stroke={arc.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            fill="none"
          />
        ))}
      </Svg>
      <View style={styles.gaugeCenter} pointerEvents="none">
        <AppText style={styles.donutValue} weight={FontWeight.bold}>{centerValue}</AppText>
        <AppText style={styles.donutLabel} color={Colors.gray600}>{centerLabel}</AppText>
      </View>
    </View>
  );
}

type BarDatum = {
  label: string;
  value: number;
  color: string;
};

type BarChartProps = {
  data: BarDatum[];
  height?: number;
};

export function BarChart({ data, height = 140 }: BarChartProps) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <View style={[styles.barChart, { height }]}>
      {data.map((bar) => (
        <View key={bar.label} style={styles.barColumn}>
          <AppText style={styles.barValue} color={Colors.gray600}>{bar.value}</AppText>
          <View style={styles.barTrack}>
            <View
              style={[
                styles.barFill,
                { height: `${Math.max((bar.value / max) * 100, 4)}%`, backgroundColor: bar.color },
              ]}
            />
          </View>
          <AppText style={styles.barLabel} color={Colors.gray600}>{bar.label}</AppText>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  donutWrap: { alignItems: "center", justifyContent: "center" },
  donutCenter: { position: "absolute", alignItems: "center" },
  gaugeCenter: { position: "absolute", bottom: 0, alignItems: "center", width: "100%" },
  donutValue: { fontSize: Fonts.h1 },
  donutLabel: { fontSize: Fonts.overline, letterSpacing: 0.5, marginTop: 2 },
  barChart: { flexDirection: "row", alignItems: "flex-end", justifyContent: "space-around", paddingTop: 8 },
  barColumn: { alignItems: "center", flex: 1, height: "100%", justifyContent: "flex-end", gap: 6 },
  barValue: { fontSize: Fonts.overline },
  barTrack: { width: 28, flex: 1, justifyContent: "flex-end" },
  barFill: { width: "100%", borderTopLeftRadius: 6, borderTopRightRadius: 6, minHeight: 4 },
  barLabel: { fontSize: Fonts.overline },
});
