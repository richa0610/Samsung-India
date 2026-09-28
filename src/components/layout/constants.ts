import { LogBox } from "react-native";
import * as SplashScreen from "expo-splash-screen";
import * as SystemUI from "expo-system-ui";

import { Colors } from "@/theme";

LogBox.ignoreLogs([
  "Expo CLI and the android client are out of sync",
  "Expo CLI and the iOS client are out of sync",
  "out of sync. Reload to reconnect",
]);

// Native calls made at module load: if the JS runtime is reloaded while one is
// still in flight, its native promise is destroyed and rejects ("JPromise was
// destroyed"). Nothing depends on the result, so swallow it.
SplashScreen.preventAutoHideAsync().catch(() => {});

SystemUI.setBackgroundColorAsync(Colors.background).catch(() => {});

export const TRAINER_ROUTES = [
  "/admin_dashboard",
  "/trainer_dashboard",
  "/add_training",
  "/pending_trainings",
  "/training_list",
  "/sessions",
  "/session_dashboard",
];
