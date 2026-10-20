import { useEffect } from "react";
import { useRouter } from "expo-router";

import LoginLandingScreen from "@/components/auth/LoginLandingScreen";
import BrandSplash from "@/components/common/BrandSplash";
import { useAuth } from "@/hooks/useAuth";

export default function HomeScreen() {
  const router = useRouter();
  const { restoring, token, adminToken, admin } = useAuth();

  useEffect(() => {
    if (restoring) return;

    if (adminToken) {
      if (admin?.role === "admin") {
        router.replace("/admin_dashboard");
      } else {
        router.replace("/trainer_dashboard");
      }
    } else if (token) {
      router.replace("/session_detail" as any);
    }
  }, [restoring, token, adminToken, admin, router]);

  // Hold the splash screen while restoring auth state from storage or while
  // routing an authenticated user to their dashboard, avoiding login screen flashes.
  if (restoring || adminToken || token) {
    return <BrandSplash />;
  }

  return <LoginLandingScreen />;
}
