import { useLocalSearchParams } from "expo-router";

import StaffLoginScreen from "@/components/auth/staff-login/StaffLoginScreen";

export default function TrainerLoginScreen() {
  // `portal=admin` when reached through Login as -> Admin; `reason` e.g. "session_expired".
  // Both roles sign in here - the server's role decides admin_dashboard vs trainer_dashboard.
  const { reason, portal } = useLocalSearchParams<{ reason?: string; portal?: string }>();
  return <StaffLoginScreen portal={portal === "admin" ? "admin" : "trainer"} reason={reason} />;
}
