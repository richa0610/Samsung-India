import { useRouter } from "expo-router";
import { StyleSheet } from "react-native";

import AppModal from "@/components/ui/AppModal";
import MoreMenuGrid from "./MoreMenuGrid";

const pad2 = (n: number) => String(n).padStart(2, "0");
export const toApiDate = (d: Date) =>
  `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

// Shared by the bottom nav's "More" menu and the dashboard's quick-actions
// panel, which uses slightly different (pluralized) labels for a few items.
export function useTrainerNavigate() {
  const router = useRouter();

  return (label: string) => {
    if (label === "Add New Trainings" || label === "New Training") {
      router.push("/add_training");
    } else if (label === "Pending Trainings" || label === "Pending Training") {
      router.push("/pending_trainings");
    } else if (label === "Training List") {
      router.push("/training_list");
    } else if (label === "Attendance List") {
      router.push("/attendance_list");
    } else if (label === "New Trainee") {
      router.push("/new_trainee");
    } else if (label === "Trainee List") {
      router.push("/trainee_list");
    } else if (label === "Pending Trainee") {
      router.push("/pending_trainee");
    } else if (label === "Confirmed Attendance") {
      router.push("/confirmed_attendance");
    } else if (label === "Pending Attendance") {
      router.push("/pending_attendance");
    } else if (label === "View Sessions") {
      // No date params - lands on the Sessions screen's own "All" default,
      // not silently scoped to whatever the dashboard calendar's current
      // range happens to be.
      router.push("/sessions");
    } else if (label === "View Reports") {
      // Same reasoning as "View Sessions" above - only the tab is forced
      // (Completed), no incidental date scoping.
      router.push({ pathname: "/sessions", params: { tab: "completed" } });
    }
  };
}

type TrainerMoreMenuProps = {
  visible: boolean;
  onClose: () => void;
};

export default function TrainerMoreMenu({ visible, onClose }: TrainerMoreMenuProps) {
  const handleNavigate = useTrainerNavigate();

  return (
    <AppModal visible={visible} onClose={onClose} position="bottom" contentStyle={styles.sheet}>
      <MoreMenuGrid
        onSelect={(label) => {
          onClose();
          handleNavigate(label);
        }}
      />
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { width: "100%" },
});
