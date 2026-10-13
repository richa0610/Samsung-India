import { StyleSheet } from "react-native";
import Svg, { G, Path } from "react-native-svg";

import { Colors } from "@/theme/colors";

const LEFT_LINES = 12;
const RIGHT_LINES = 10;

/** One ribbon of thin, slightly fanned curves; `curve(t)` draws the line at t (0 = first, 1 = last). */
function Ribbon({ count, curve }: { count: number; curve: (t: number) => string }) {
  return (
    <G>
      {Array.from({ length: count }, (_, i) => (
        <Path key={i} d={curve(i / (count - 1))} />
      ))}
    </G>
  );
}

/** The login landing footer's background, from the design: two faint ribbons of fine lines - one
 *  sweeping down from the left edge, one rising to the right edge - behind the footer logo.
 *  Decorative only. */
export default function FooterWaves({ width: W, height: H }: { width: number; height: number }) {
  const left = (t: number) =>
    `M0 ${H * (0.1 + 0.45 * t)} C ${W * 0.18} ${H * (0.12 + 0.45 * t)}, ${W * 0.28} ${H * (0.85 + 0.1 * t)}, ${W * (0.42 - 0.12 * t)} ${H + 2}`;
  const right = (t: number) =>
    `M${W * (0.55 + 0.1 * t)} ${H + 2} C ${W * 0.72} ${H * 0.9}, ${W * 0.85} ${H * (0.62 + 0.15 * t)}, ${W} ${H * (0.6 + 0.2 * t)}`;
  return (
    <Svg width={W} height={H} style={styles.waves} pointerEvents="none">
      <G fill="none" stroke={Colors.heroWaveMist} strokeOpacity={0.45} strokeWidth={1}>
        <Ribbon count={LEFT_LINES} curve={left} />
        <Ribbon count={RIGHT_LINES} curve={right} />
      </G>
    </Svg>
  );
}

const styles = StyleSheet.create({
  waves: { position: "absolute", left: 0, bottom: 0 },
});
