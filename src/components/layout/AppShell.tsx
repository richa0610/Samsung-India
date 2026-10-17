import { ReactNode } from "react";
import { Platform, StyleSheet, View } from "react-native";

import { Breakpoints, Colors, Shadows } from "@/theme";

interface AppShellProps {
  isTrainerRoute: boolean;
  children: ReactNode;
}

export function AppShell({ isTrainerRoute, children }: AppShellProps) {
  const isWeb = Platform.OS === "web";

  return (
    <View style={[styles.root, isWeb && styles.webRoot]}>
      <View
        style={[
          styles.appContainer,
          isWeb && (isTrainerRoute ? styles.webTrainerContainer : styles.webMobileContainer),
        ]}
      >
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  webRoot: {
    backgroundColor: Colors.slate200,
    minHeight: "100%",
  },
  appContainer: {
    flex: 1,
    width: "100%",
  },
  webMobileContainer: {
    maxWidth: Breakpoints.mobileMaxWidth,
    width: "100%",
    marginHorizontal: "auto",
    backgroundColor: Colors.background,
    ...Shadows.webContainer,
  },
  webTrainerContainer: {
    maxWidth: Breakpoints.trainerMaxWidth,
    width: "100%",
    marginHorizontal: "auto",
    backgroundColor: Colors.gray50,
    ...Shadows.webContainer,
  },
});
