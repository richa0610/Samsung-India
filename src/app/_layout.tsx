import { DefaultTheme, ThemeProvider, usePathname } from "expo-router";

import { AnimatedSplashOverlay } from "@/components/animated-icon";
import BrandSplash from "@/components/common/BrandSplash";
import { AppShell, AppStack, TRAINER_ROUTES, useRouteBlur } from "@/components/layout";
import { AdminFiltersProvider } from "@/hooks/useAdminFilters";
import { AuthProvider } from "@/hooks/useAuth";
import { useAppFonts } from "@/hooks/useAppFonts";

export default function RootLayout() {
  const pathname = usePathname();
  const { fontsLoaded, fontError } = useAppFonts();
  useRouteBlur(pathname);

  if (!fontsLoaded && !fontError) {
    return <BrandSplash />;
  }

  const isTrainerRoute = TRAINER_ROUTES.some((route) => pathname?.startsWith(route));

  return (
    <AuthProvider>
      <AdminFiltersProvider>
      <ThemeProvider value={DefaultTheme}>
        <AnimatedSplashOverlay />
        <AppShell isTrainerRoute={isTrainerRoute}>
          <AppStack />
        </AppShell>
      </ThemeProvider>
    </AdminFiltersProvider>
    </AuthProvider>
  );
}
