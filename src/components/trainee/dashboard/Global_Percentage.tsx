import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

export type GlobalPercentageProps = {
  percentage?: number;
  totalScore?: number;
  maxScore?: number;
  periodGain?: number | null;
  globalRank?: string;
  globalPercentile?: number;
  stateRank?: string;
  statePercentile?: number;
};

export default function Global_Percentage({
  percentage = 0,
  totalScore = 0,
  maxScore = 0,
  periodGain = null,
  globalRank = "—",
  globalPercentile = 0,
  stateRank = "—",
  statePercentile = 0,
}: GlobalPercentageProps) {
  const size = 122;
  const strokeWidth = 13;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <View style={styles.container}>
      {/* Left Card: Global Percentage */}
      <View style={styles.globalCard}>
        <AppText variant="caption" weight={FontWeight.bold} color="#111827" style={styles.cardTitle}>
          Overall Performance
        </AppText>

        {/* Circular Donut Gauge */}
        <View style={styles.chartWrapper}>
          <View style={{ width: size, height: size, transform: [{ rotate: "-90deg" }] }}>
            <Svg width={size} height={size}>
              <Circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke="#E5E7EB"
                strokeWidth={strokeWidth}
                fill="none"
              />
              <Circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke="#0066FF"
                strokeWidth={strokeWidth}
                strokeDasharray={`${circumference} ${circumference}`}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="none"
              />
            </Svg>
          </View>

          <View style={styles.donutCenter} pointerEvents="none">
            <AppText variant="h2" weight={FontWeight.bold} color="#111827" style={styles.pctText}>
              {percentage}%
            </AppText>
            <AppText variant="tiny" color="#4B5563" weight={FontWeight.medium} style={styles.scoreRatio}>
              {totalScore} / {maxScore}
            </AppText>
            <AppText variant="tiny" color="#9CA3AF" style={styles.scoreLabel}>
              Total Score
            </AppText>
          </View>
        </View>

        {/* Footer Meta */}
        <View style={styles.footerMeta}>
          <AppText variant="tiny" color="#6B7280" style={styles.footerCaption}>
            Score from all questions
          </AppText>
          {periodGain != null && periodGain !== 0 && (
            <AppText
              variant="tiny"
              color={periodGain > 0 ? "#16A34A" : "#DC2626"}
              weight={FontWeight.bold}
              style={styles.footerGain}
            >
              {periodGain > 0 ? "▲" : "▼"} {Math.abs(periodGain)} points this period
            </AppText>
          )}
        </View>
      </View>

      {/* Right Card: Ranking */}
      <View style={styles.rankingCard}>
        {/* Header */}
        <View style={styles.rankingHeader}>
          <View style={styles.trophyWrap}>
            <Ionicons name="trophy-outline" size={15} color="#7C3AED" />
          </View>
          <AppText variant="caption" weight={FontWeight.bold} color="#111827" style={styles.cardTitle}>
            Ranking
          </AppText>
        </View>

        {/* Global Ranking Box */}
        <View style={styles.rankBox}>
          <View style={styles.rankRow}>
            <View style={[styles.iconCircle, { backgroundColor: "#EFF6FF" }]}>
              <Ionicons name="globe-outline" size={16} color="#2563EB" />
            </View>
            <View style={styles.rankMeta}>
              <AppText variant="tiny" weight={FontWeight.bold} color="#1F2937">
                Global Ranking
              </AppText>
            </View>
            <View style={styles.rankBadge}>
              <AppText variant="tiny" weight={FontWeight.bold} color="#1D4ED8">
                {globalRank}
              </AppText>
              <Ionicons name="chevron-forward" size={13} color="#6B7280" />
            </View>
          </View>

          {/* Slider */}
          <View style={styles.sliderSection}>
            <View style={styles.sliderTrack}>
              <View style={[styles.sliderFill, { width: `${globalPercentile}%`, backgroundColor: "#0066FF" }]} />
              <View style={[styles.sliderThumb, { left: `${globalPercentile}%`, backgroundColor: "#0066FF" }]} />
            </View>
            <View style={styles.sliderLabels}>
              <AppText variant="tiny" color="#9CA3AF" style={styles.sliderLabelText}>Top 1%</AppText>
              <AppText variant="tiny" color="#9CA3AF" style={styles.sliderLabelText}>Top 100%</AppText>
            </View>
          </View>
        </View>

        {/* State Ranking Box */}
        <View style={styles.rankBox}>
          <View style={styles.rankRow}>
            <View style={[styles.iconCircle, { backgroundColor: "#FAF5FF" }]}>
              <Ionicons name="location-outline" size={16} color="#475569" />
            </View>
            <View style={styles.rankMeta}>
              <AppText variant="tiny" weight={FontWeight.bold} color="#1F2937">
                State Ranking
              </AppText>
            </View>
            <View style={styles.rankBadge}>
              <AppText variant="caption" weight={FontWeight.bold} color="#7E22CE">
                {stateRank}
              </AppText>
              <Ionicons name="chevron-forward" size={13} color="#6B7280" />
            </View>
          </View>

          {/* Slider */}
          <View style={styles.sliderSection}>
            <View style={styles.sliderTrack}>
              <View style={[styles.sliderFill, { width: `${statePercentile}%`, backgroundColor: "#7E22CE" }]} />
              <View style={[styles.sliderThumb, { left: `${statePercentile}%`, backgroundColor: "#7E22CE" }]} />
            </View>
            <View style={styles.sliderLabels}>
              <AppText variant="tiny" color="#9CA3AF" style={styles.sliderLabelText}>Top 1%</AppText>
              <AppText variant="tiny" color="#9CA3AF" style={styles.sliderLabelText}>Top 100%</AppText>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: 16,
    marginTop: 14,
  },
  globalCard: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    ...Shadows.card,
  },
  rankingCard: {
    flex: 1.25,
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    gap: 8,
    ...Shadows.card,
  },
  cardTitle: {
    fontSize: 13,
  },
  chartWrapper: {
    alignItems: "center",
    justifyContent: "center",
    marginVertical: 4,
    position: "relative",
  },
  donutCenter: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  pctText: {
    fontSize: 22,
    lineHeight: 26,
  },
  scoreRatio: {
    fontSize: 10,
    marginTop: 1,
  },
  scoreLabel: {
    fontSize: 8.5,
  },
  footerMeta: {
    alignItems: "center",
    marginTop: 4,
    gap: 1,
  },
  footerCaption: {
    fontSize: 9.5,
  },
  footerGain: {
    fontSize: 10,
  },
  rankingHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  trophyWrap: {
    width: 26,
    height: 26,
    borderRadius: 6,
    backgroundColor: "#F3E8FF",
    alignItems: "center",
    justifyContent: "center",
  },
  rankBox: {
    backgroundColor: Colors.white,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#F1F5F9",
    padding: 8,
    gap: 6,
  },
  rankRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  iconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  rankMeta: {
    flex: 1,
  },
  rankBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 1,
  },
  sliderSection: {
    marginTop: 1,
  },
  sliderTrack: {
    height: 4,
    backgroundColor: "#E2E8F0",
    borderRadius: 2,
    position: "relative",
    justifyContent: "center",
  },
  sliderFill: {
    height: "100%",
    borderRadius: 2,
  },
  sliderThumb: {
    position: "absolute",
    width: 8,
    height: 8,
    borderRadius: 4,
    top: -2,
    marginLeft: -4,
    borderWidth: 1.5,
    borderColor: Colors.white,
  },
  sliderLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 2,
  },
  sliderLabelText: {
    fontSize: 8,
  },
});
