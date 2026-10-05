import { View } from "react-native";
import Svg, { Circle, Defs, G, Line, LinearGradient, Path, Rect, Stop } from "react-native-svg";

import { Colors } from "@/theme/colors";

/** The illustration's drawing grid; it is drawn at whatever width it is given, keeping this shape. */
export const ILLUSTRATION_WIDTH = 180;
export const ILLUSTRATION_HEIGHT = 220;

/** A small four-point sparkle centred on (x, y). */
const sparkle = (x: number, y: number, r: number) =>
  `M${x} ${y - r} Q${x} ${y} ${x + r} ${y} Q${x} ${y} ${x} ${y + r} Q${x} ${y} ${x - r} ${y} Q${x} ${y} ${x} ${y - r} Z`;

/** One checklist row on the phone's screen: a ticked box and two text lines, top edge at `y`. */
function ChecklistRow({ y, long }: { y: number; long?: boolean }) {
  return (
    <G>
      <Rect x={66} y={y} width={12} height={12} rx={3} fill={Colors.illustrationSky} />
      <Path
        d={`M69 ${y + 6.2} l2.4 2.4 l4.6 -5`}
        stroke={Colors.white}
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <Rect x={84} y={y + 1.5} width={long ? 46 : 38} height={4} rx={2} fill={Colors.illustrationLine} />
      <Rect x={84} y={y + 7.5} width={long ? 32 : 26} height={3.5} rx={1.75} fill={Colors.illustrationLineSoft} />
    </G>
  );
}

/** A phone showing a course (graduation cap + checklist) with chart, document and idea tiles
 *  floating around it - vector art, so it stays sharp at any size and needs no image file.
 *  Decorative only. */
export default function LoginHeroIllustration({ width = ILLUSTRATION_WIDTH }: { width?: number }) {
  const height = (width * ILLUSTRATION_HEIGHT) / ILLUSTRATION_WIDTH;
  return (
    <View accessible={false} importantForAccessibility="no-hide-descendants">
      <Svg width={width} height={height} viewBox={`0 0 ${ILLUSTRATION_WIDTH} ${ILLUSTRATION_HEIGHT}`}>
        <Defs>
          <LinearGradient id="illPhone" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={Colors.illustrationPhoneLight} />
            <Stop offset="1" stopColor={Colors.illustrationPhoneDeep} />
          </LinearGradient>
          <LinearGradient id="illScreen" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={Colors.white} />
            <Stop offset="1" stopColor={Colors.illustrationScreenTint} />
          </LinearGradient>
          <LinearGradient id="illWhiteTile" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={Colors.white} />
            <Stop offset="1" stopColor={Colors.illustrationScreenTint} />
          </LinearGradient>
          <LinearGradient id="illPurpleTile" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={Colors.illustrationPurpleLight} />
            <Stop offset="1" stopColor={Colors.illustrationPurple} />
          </LinearGradient>
          <LinearGradient id="illBlueTile" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={Colors.illustrationSkyLight} />
            <Stop offset="1" stopColor={Colors.illustrationSky} />
          </LinearGradient>
        </Defs>

        {/* The phone, tilted to the right */}
        <G rotation={10} origin="100, 110">
          <Rect x={54} y={23} width={104} height={188} rx={22} fill={Colors.illustrationShadow} opacity={0.28} />
          <Rect x={48} y={16} width={104} height={188} rx={22} fill="url(#illPhone)" />
          <Rect x={50} y={18} width={100} height={184} rx={20} fill="none" stroke={Colors.white} strokeOpacity={0.3} strokeWidth={1} />
          <Rect x={56} y={26} width={88} height={168} rx={15} fill="url(#illScreen)" />
          <Rect x={86} y={30} width={28} height={6} rx={3} fill={Colors.illustrationPhoneDeep} opacity={0.85} />

          {/* Graduation cap */}
          <Path d="M86 67 L86 77 Q100 85 114 77 L114 67 L100 73 Z" fill={Colors.illustrationPhoneDeep} />
          <Path d="M100 48 L127 60 L100 72 L73 60 Z" fill={Colors.illustrationNavy} />
          <Path d="M100 48 L127 60 L100 64 L73 60 Z" fill={Colors.illustrationPhoneDeep} opacity={0.55} />
          <Line x1={122} y1={62} x2={122} y2={75} stroke={Colors.illustrationGold} strokeWidth={2} strokeLinecap="round" />
          <Circle cx={122} cy={76.5} r={2.6} fill={Colors.illustrationGold} />

          <ChecklistRow y={96} long />
          <ChecklistRow y={118} />
          <ChecklistRow y={140} long />
          <Rect x={86} y={184} width={28} height={3} rx={1.5} fill={Colors.illustrationLineSoft} />
        </G>

        {/* Chart tile - floating top-left */}
        <G rotation={-10} origin="28, 54">
          <Rect x={8} y={35} width={48} height={48} rx={12} fill={Colors.illustrationShadow} opacity={0.22} />
          <Rect x={4} y={30} width={48} height={48} rx={12} fill="url(#illWhiteTile)" />
          <Rect x={14} y={56} width={6} height={10} rx={2} fill={Colors.illustrationSkyLight} />
          <Rect x={23} y={48} width={6} height={18} rx={2} fill={Colors.illustrationSky} />
          <Rect x={32} y={40} width={6} height={26} rx={2} fill={Colors.illustrationPhoneDeep} />
          <Rect x={12} y={67} width={28} height={2} rx={1} fill={Colors.illustrationLineSoft} />
        </G>

        {/* Document tile - lower-left, in front of the phone */}
        <G rotation={-12} origin="38, 175">
          <Rect x={20} y={155} width={44} height={50} rx={12} fill={Colors.illustrationShadow} opacity={0.22} />
          <Rect x={16} y={150} width={44} height={50} rx={12} fill="url(#illPurpleTile)" />
          <Path d="M26 160 L44 160 L50 166 L50 190 L26 190 Z" fill={Colors.white} />
          <Path d="M44 160 L50 166 L44 166 Z" fill={Colors.illustrationPurpleTint} />
          <Rect x={30} y={170} width={16} height={2.5} rx={1.25} fill={Colors.illustrationPurpleLight} />
          <Rect x={30} y={175} width={16} height={2.5} rx={1.25} fill={Colors.illustrationPurpleLight} />
          <Rect x={30} y={180} width={11} height={2.5} rx={1.25} fill={Colors.illustrationPurpleLight} />
        </G>

        {/* Idea tile - right, in front of the phone */}
        <G rotation={10} origin="155, 135">
          <Rect x={136} y={117} width={46} height={46} rx={12} fill={Colors.illustrationShadow} opacity={0.22} />
          <Rect x={132} y={112} width={46} height={46} rx={12} fill="url(#illBlueTile)" />
          <Circle cx={155} cy={131} r={13} fill={Colors.illustrationGlow} opacity={0.3} />
          <Circle cx={155} cy={131} r={7.5} fill={Colors.illustrationGlow} />
          <Rect x={151.5} y={137} width={7} height={3} rx={1} fill={Colors.white} />
          <Rect x={152.5} y={140.5} width={5} height={2.5} rx={1} fill={Colors.illustrationScreenTint} />
          <G stroke={Colors.illustrationGlow} strokeWidth={1.6} strokeLinecap="round">
            <Line x1={155} y1={117.5} x2={155} y2={120.5} />
            <Line x1={141.5} y1={131} x2={144.5} y2={131} />
            <Line x1={165.5} y1={131} x2={168.5} y2={131} />
            <Line x1={145.6} y1={121.6} x2={147.7} y2={123.7} />
            <Line x1={164.4} y1={121.6} x2={162.3} y2={123.7} />
          </G>
        </G>

        {/* Sparkles */}
        <Path d={sparkle(30, 14, 5)} fill={Colors.white} opacity={0.85} />
        <Path d={sparkle(172, 88, 4)} fill={Colors.white} opacity={0.75} />
        <Path d={sparkle(14, 120, 3)} fill={Colors.white} opacity={0.6} />
      </Svg>
    </View>
  );
}
