import { LogBox } from "react-native";
import * as SplashScreen from "expo-splash-screen";
import * as SystemUI from "expo-system-ui";

import { Colors } from "@/theme";

LogBox.ignoreLogs([
  "Expo CLI and the android client are out of sync",
  "Expo CLI and the iOS client are out of sync",
  "out of sync. Reload to reconnect",
]);

SplashScreen.preventAutoHideAsync();

SystemUI.setBackgroundColorAsync(Colors.background);

export const TRAINER_ROUTES = [
  "/admin_dashboard",
  "/trainer_dashboard",
  "/assessment_builder",
  "/add_training",
  "/pending_trainings",
  "/training_list",
  "/sessions",
  "/session_dashboard",
];
