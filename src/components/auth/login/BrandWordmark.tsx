import { StyleSheet, View } from "react-native";
import Svg, { G, Path } from "react-native-svg";

import AppText from "@/components/ui/AppText";
import { BRAND } from "@/constants/strings";

type Props = {
  color: string;
  /** "large" on the hero banner, "small" in the footer. */
  size?: "large" | "small";
  align?: "left" | "center";
};

// The name is drawn as wide, heavy geometric letters (an extended logotype like SAMSUNG's) so it
// looks the same on every phone - fonts can't be stretched reliably on Android. Each letter is a
// set of stroke centre-lines on a 14-unit cap height; any letter not drawn here falls back to text.
const CAP = 14;
const STROKE = 3.4;
const HALF = STROKE / 2;
const LETTER_GAP = 2.8;

type Glyph = { advance: number; paths: string[] };

const GLYPHS: Record<string, Glyph> = (() => {
  const r = (CAP - STROKE) / 2; // O: a stadium
  const bowl = 3.65; // P: its bowl's radius
  const sr = (CAP / 2 - HALF) / 2; // S: its two turns' radius
  const sl = HALF;
  const sx = 15 - HALF;
  return {
    T: { advance: 15, paths: [`M0 ${HALF} H15`, `M7.5 ${HALF} V${CAP}`] },
    O: {
      advance: 18,
      paths: [
        `M${HALF + r} ${HALF} H${18 - HALF - r} A${r} ${r} 0 0 1 ${18 - HALF - r} ${CAP - HALF} H${HALF + r} A${r} ${r} 0 0 1 ${HALF + r} ${HALF} Z`,
      ],
    },
    P: {
      advance: 15,
      paths: [`M${HALF} ${CAP} V${HALF} H${15 - HALF - bowl} A${bowl} ${bowl} 0 0 1 ${15 - HALF - bowl} ${HALF + 2 * bowl} H${HALF}`],
    },
    S: {
      advance: 15,
      paths: [
        `M${sx} ${HALF} H${sl + sr} A${sr} ${sr} 0 0 0 ${sl + sr} ${CAP / 2} H${sx - sr} A${sr} ${sr} 0 0 1 ${sx - sr} ${CAP - HALF} H${sl}`,
      ],
    },
  };
})();

const SIZES = {
  large: { width: 92, regionSize: 8.5, regionSpacing: 5.6, regionGap: 6, fallbackSize: 18 },
  small: { width: 68, regionSize: 7, regionSpacing: 4.4, regionGap: 4, fallbackSize: 14 },
} as const;

function DrawnName({ name, color, width }: { name: string; color: string; width: number }) {
  let x = 0;
  const placed = [...name].map((letter) => {
    const glyph = GLYPHS[letter];
    const at = x;
    x += glyph.advance + LETTER_GAP;
    return { letter, glyph, at };
  });
  const total = x - LETTER_GAP;
  return (
    <Svg width={width} height={(width * CAP) / total} viewBox={`0 0 ${total} ${CAP}`}>
      {placed.map(({ letter, glyph, at }, i) => (
        <G key={`${letter}${i}`} transform={`translate(${at} 0)`}>
          {glyph.paths.map((d) => (
            <Path key={d} d={d} stroke={color} strokeWidth={STROKE} fill="none" strokeLinejoin="miter" />
          ))}
        </G>
      ))}
    </Svg>
  );
}

/** The brand's logotype: the name in wide heavy capitals with its spaced-out region line underneath
 *  (e.g. TOPS / I N D I A). Text comes from BRAND. */
export default function BrandWordmark({ color, size = "large", align = "left" }: Props) {
  const s = SIZES[size];
  const drawable = [...BRAND.name].every((letter) => letter in GLYPHS);
  const centered = align === "center";

  return (
    <View
      style={centered ? styles.centered : styles.left}
      accessible
      accessibilityRole="image"
      accessibilityLabel={BRAND.region ? `${BRAND.name} ${BRAND.region}` : BRAND.name}
    >
      {drawable ? (
        <DrawnName name={BRAND.name} color={color} width={s.width} />
      ) : (
        <AppText color={color} style={{ fontSize: s.fallbackSize, fontWeight: "900", letterSpacing: 3 }}>
          {BRAND.name}
        </AppText>
      )}
      {BRAND.region ? (
        <AppText
          color={color}
          style={{
            fontSize: s.regionSize,
            lineHeight: s.regionSize * 1.3,
            fontWeight: "600",
            letterSpacing: s.regionSpacing,
            marginTop: s.regionGap,
            // Letter spacing also trails the last letter; balance it so a centred line stays centred.
            paddingLeft: centered ? s.regionSpacing : 0,
          }}
        >
          {BRAND.region}
        </AppText>
      ) : null}
    </View>

  );
}

const styles = StyleSheet.create({
  left: { alignSelf: "flex-start", alignItems: "flex-start" },
  centered: { alignSelf: "center", alignItems: "center" },
});
