import { ReactNode, useState } from "react";
import { StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { Image, ImageContentFit, ImageStyle } from "expo-image";
import { Ionicons } from "@expo/vector-icons";

import { useAuth } from "@/hooks/useAuth";
import { resolveMediaUrl } from "@/utils/media";
import AppText from "./AppText";
import { Colors } from "@/theme/colors";

type MediaImageProps = {
  /** Relative media path (e.g. "trainer_checkin_photos/CONF123.jpg") or an
   *  already-absolute URL - both go through resolveMediaUrl. */
  path?: string | null;
  // Accepts the same plain box styles (width/height/borderRadius/etc.) either
  // an Image or a View can take - callers pass one style value for both the
  // real image and the fallback View, so this stays permissive rather than
  // forcing two separate style props.
  style?: StyleProp<ImageStyle>;
  contentFit?: ImageContentFit;
  /** Replaces the default "Image not found" box on failure - e.g. a small
   *  circular avatar should fall back to a plain icon instead of wrapping
   *  that text into a 60px circle. */
  fallback?: ReactNode;
};

/** Shared authenticated-media viewer: every /media/* route requires a bearer
 *  token (see backend/app/routers/media.py), and this is the one place that
 *  attaches it and shows a clean "Image not found" state instead of a blank
 *  box or a raw error whenever a photo fails to load - whether that's a
 *  genuinely missing file (404, e.g. lost from local disk storage) or a
 *  network/auth problem. cachePolicy="none" avoids a subtle trap: expo-image
 *  caches by URL, so a URL that ever failed once (e.g. before an auth fix
 *  shipped) would otherwise keep serving that stale failure forever. */
export default function MediaImage({ path, style, contentFit = "cover", fallback }: MediaImageProps) {
  const { adminToken, token } = useAuth();
  const authToken = adminToken ?? token;
  const url = resolveMediaUrl(path);
  const [failed, setFailed] = useState(false);

  if (!url || failed) {
    if (fallback) return <>{fallback}</>;
    return (
      <View style={[styles.fallback, style as StyleProp<ViewStyle>]}>
        <Ionicons name="image-outline" size={22} color={Colors.gray400} />
        <AppText style={styles.fallbackText} color={Colors.gray400}>
          Image not found
        </AppText>
      </View>
    );
  }

  return (
    <Image
      source={{ uri: url, headers: authToken ? { Authorization: `Bearer ${authToken}` } : undefined }}
      style={style}
      contentFit={contentFit}
      cachePolicy="none"
      onError={() => setFailed(true)}
    />
  );
}

const styles = StyleSheet.create({
  fallback: {
    backgroundColor: Colors.gray100,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  fallbackText: { fontSize: 12 },
});
