import { useEffect } from "react";
import { Platform } from "react-native";

// Globally blur active element on route changes to eliminate aria-hidden accessibility warnings on React Native Web
export function useRouteBlur(pathname: string | null) {
  useEffect(() => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
    }
  }, [pathname]);
}
