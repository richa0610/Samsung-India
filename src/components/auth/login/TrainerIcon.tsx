import Svg, { Circle, Path } from "react-native-svg";

/** A line icon of a person presenting at a board - the "Trainer" role. No stock icon set has
 *  this exact glyph, so it is drawn (58 x 53 drawing grid, round strokes). */
export default function TrainerIcon({ size = 32, color }: { size?: number; color: string }) {
  return (
    <Svg width={size} height={(size * 53) / 58} viewBox="-2 -2 62 57">
      <Path
        d="M15.5 12.5 V1.75 H55.75 V30.75 H37.5"
        stroke={color}
        strokeWidth={3.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <Circle cx={13.75} cy={21.25} r={6.5} stroke={color} strokeWidth={3.6} fill="none" />
      <Path
        d="M2 51 V44.5 C2 40 5.6 36.5 10 36.5 H18 L37 30.5"
        stroke={color}
        strokeWidth={3.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <Path d="M26 51 V41" stroke={color} strokeWidth={3.6} strokeLinecap="round" fill="none" />
    </Svg>
  );
}
