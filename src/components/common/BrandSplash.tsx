import { Image } from "expo-image";
import { StyleSheet, View } from "react-native";

import { SPLASH_LOGO_ASPECT_RATIO, SPLASH_LOGO_WIDTH } from "@/config/splash";

/**
 * Full-screen TOPS branding shown while the app boots (fonts / auth state
 * loading) before the role-selection screen is ready. Uses no custom fonts -
 * they may not be loaded yet - the wordmark + tagline are baked into the image.
 */
export default function BrandSplash() {
  return (
    <View style={styles.container}>
      <Image
        source={require("@/assets/images/logo/project_logo.png")}
        style={styles.logo}
        contentFit="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFFFFF", alignItems: "center", justifyContent: "center" },
  logo: { width: SPLASH_LOGO_WIDTH, height: SPLASH_LOGO_WIDTH * SPLASH_LOGO_ASPECT_RATIO },
});
