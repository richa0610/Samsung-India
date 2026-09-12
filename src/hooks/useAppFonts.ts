import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

/**
 * The app renders entirely in the OS system UI font (see
 * `theme/fontFamily.ts` - `APP_FONT_FAMILY`); no custom font files are
 * bundled. This hook just dismisses the native splash on first mount and
 * keeps the `{ fontsLoaded, fontError }` shape `app/_layout.tsx` gates on.
 */
export function useAppFonts() {
  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  return { fontsLoaded: true, fontError: null as Error | null };
}
