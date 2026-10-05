import { useCallback, useEffect, useRef, useState } from "react";
import {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  useWindowDimensions,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle, Defs, LinearGradient, Path, RadialGradient, Rect, Stop } from "react-native-svg";

import AppText from "@/components/ui/AppText";
import { LOGIN_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import BrandWordmark from "./BrandWordmark";
import LoginHeroIllustration, { ILLUSTRATION_HEIGHT, ILLUSTRATION_WIDTH } from "./LoginHeroIllustration";

/** How long each slide stays before the carousel moves on by itself. */
export const SLIDE_INTERVAL_MS = 5000;
const SIDE_PADDING = 24;
/** Space under the dots before the banner fades into the page (the sky-blue swoosh sits here). */
const BOTTOM_SPACE = 64;
/** Layout of the banner, as fractions of the screen width (from the design): text on the left,
 *  the illustration on the right, never overlapping. */
const TEXT_END = 0.53;
const ILLUSTRATION_START = 0.56;
const ILLUSTRATION_END = 0.96;

const slides = LOGIN_TEXT.slides;

/** The banner's background: the design's blues (deep royal left, azure right, a lighter top-left,
 *  a sky glow low on the right), faint rings, and the sky-blue swoosh into the white page. */
function HeroBackground({ width: W, height: H }: { width: number; height: number }) {
  const swoosh =
    `M0 ${H - 58} C ${W * 0.16} ${H - 32}, ${W * 0.32} ${H - 20}, ${W * 0.5} ${H - 18} ` +
    `C ${W * 0.7} ${H - 16}, ${W * 0.84} ${H - 30}, ${W} ${H - 36} L ${W} ${H} L 0 ${H} Z`;
  return (
    <Svg width={W} height={H} style={StyleSheet.absoluteFill}>
      <Defs>
        <LinearGradient id="heroBase" x1="0" y1="0" x2="1" y2="0.25">
          <Stop offset="0" stopColor={Colors.heroBlueDeep} />
          <Stop offset="0.55" stopColor={Colors.heroBlueMid} />
          <Stop offset="1" stopColor={Colors.heroBlueBright} />
        </LinearGradient>
        <RadialGradient id="heroTopLeft" cx="0" cy="0" rx={W * 0.75} ry={H * 0.55} gradientUnits="userSpaceOnUse">
          <Stop offset="0" stopColor={Colors.heroBlueTopLeft} stopOpacity={0.9} />
          <Stop offset="1" stopColor={Colors.heroBlueTopLeft} stopOpacity={0} />
        </RadialGradient>
        <RadialGradient id="heroSky" cx={W * 0.96} cy={H * 0.8} rx={W * 0.5} ry={H * 0.42} gradientUnits="userSpaceOnUse">
          <Stop offset="0" stopColor={Colors.heroSkyGlow} stopOpacity={1} />
          <Stop offset="0.55" stopColor={Colors.heroSkyGlow} stopOpacity={0.45} />
          <Stop offset="1" stopColor={Colors.heroSkyGlow} stopOpacity={0} />
        </RadialGradient>
        <LinearGradient id="heroSwoosh" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={Colors.heroWaveSky} />
          <Stop offset="0.5" stopColor={Colors.heroWaveMist} />
          <Stop offset="1" stopColor={Colors.white} />
        </LinearGradient>
      </Defs>
      <Rect width={W} height={H} fill="url(#heroBase)" />
      <Rect width={W} height={H} fill="url(#heroTopLeft)" />
      <Rect width={W} height={H} fill="url(#heroSky)" />
      <Circle cx={W * 0.86} cy={H * 0.42} r={W * 0.36} fill="none" stroke={Colors.onHero} strokeWidth={1} opacity={0.12} />
      <Circle cx={W * 0.86} cy={H * 0.42} r={W * 0.5} fill="none" stroke={Colors.onHero} strokeWidth={1} opacity={0.07} />
      <Path d={swoosh} fill="url(#heroSwoosh)" />
    </Svg>
  );
}

/** The login landing's blue banner: the brand, a swipeable / auto-advancing message carousel on
 *  the left, the illustration on the right, and padding before the swoosh into the white page. */
export default function LoginHero() {
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [height, setHeight] = useState(0);

  const slideWidth = Math.round(width * TEXT_END) - SIDE_PADDING;
  const illustrationWidth = Math.round(width * (ILLUSTRATION_END - ILLUSTRATION_START));
  const illustrationHeight = (illustrationWidth * ILLUSTRATION_HEIGHT) / ILLUSTRATION_WIDTH;

  const scrollRef = useRef<ScrollView>(null);
  const [index, setIndex] = useState(0);

  const goTo = useCallback(
    (next: number) => {
      scrollRef.current?.scrollTo({ x: next * slideWidth, animated: true });
      setIndex(next);
    },
    [slideWidth],
  );

  // Moves on by itself; any change of slide (a swipe or a dot tap) restarts the wait.
  useEffect(() => {
    const timer = setTimeout(() => goTo((index + 1) % slides.length), SLIDE_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [index, goTo]);

  const onSwipeEnd = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    setIndex(Math.round(event.nativeEvent.contentOffset.x / slideWidth));
  };

  // The banner is as tall as its content (+ the bottom space); the background is drawn to match.
  const onLayout = (event: LayoutChangeEvent) => setHeight(Math.round(event.nativeEvent.layout.height));

  return (
    <View onLayout={onLayout} style={[styles.hero, { paddingTop: insets.top + 24 }]}>
      {height > 0 && <HeroBackground width={width} height={height} />}

      <View style={styles.brandRow}>
        <BrandWordmark color={Colors.onHero} />
      </View>

      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onSwipeEnd}
        style={[styles.slides, { width: slideWidth }]}
      >
        {slides.map((slide) => (
          <View key={slide.headline} style={{ width: slideWidth }}>
            <AppText variant="hero" color={Colors.onHero}>
              {slide.headline}
            </AppText>
            <AppText variant="heroBody" color={Colors.onHeroMuted} style={styles.slideBody}>
              {slide.body}
            </AppText>
          </View>
        ))}
      </ScrollView>

      <View style={styles.dots}>
        {slides.map((slide, i) => (
          <Pressable
            key={slide.headline}
            onPress={() => goTo(i)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`Show slide ${i + 1} of ${slides.length}`}
            accessibilityState={{ selected: i === index }}
            testID={`login-slide-dot-${i}`}
          >
            <View style={[styles.dot, i === index && styles.dotActive]} />
          </Pressable>
        ))}
      </View>

      <View
        pointerEvents="none"
        style={[
          styles.illustration,
          { top: insets.top + 36, left: width * ILLUSTRATION_START, width: illustrationWidth, height: illustrationHeight },
        ]}
      >
        <LoginHeroIllustration width={illustrationWidth} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: { paddingBottom: BOTTOM_SPACE, overflow: "hidden" },
  brandRow: { paddingHorizontal: SIDE_PADDING },
  slides: { marginTop: 40, marginLeft: SIDE_PADDING, flexGrow: 0 },
  slideBody: { marginTop: 10 },
  illustration: { position: "absolute" },
  dots: { flexDirection: "row", justifyContent: "center", gap: 10, marginTop: 26 },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: Colors.onHeroFaint },
  dotActive: { backgroundColor: Colors.onHero },
});
