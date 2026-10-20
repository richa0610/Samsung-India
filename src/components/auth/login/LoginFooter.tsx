import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { BRAND } from "@/constants/strings";
import { Colors } from "@/theme/colors";

import BrandWordmark from "./BrandWordmark";
import FooterWaves from "./FooterWaves";

const FOOTER_WAVE_HEIGHT = 150;

/** The sign-in screens' footer: the waves, the small wordmark and the tagline - pushed to the
 *  bottom of the page (inside a ScrollView whose content grows to fill it). */
export default function LoginFooter() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();

  return (
    <View style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}>
      <FooterWaves width={width} height={FOOTER_WAVE_HEIGHT} />
      <BrandWordmark color={Colors.brandWordmark} size="small" align="center" />
      <AppText variant="caption" color={Colors.loginSubtext} style={styles.tagline}>
        {BRAND.tagline.join("  |  ")}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  footer: { marginTop: "auto", paddingTop: 72, alignItems: "center", overflow: "hidden" },
  tagline: { marginTop: 8 },
});
