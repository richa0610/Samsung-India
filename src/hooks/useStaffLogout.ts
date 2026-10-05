import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { BackHandler } from "react-native";

import { useAuth } from "@/hooks/useAuth";

/**
 * Confirm-before-logout for staff (admin and trainer) screens.
 *
 * The header's power button opens the confirmation; logging out only happens on confirm,
 * then lands on the role chooser. On the home screens (`confirmOnBack`, the default) the
 * hardware/gesture back button opens the same confirmation instead of leaving - screens
 * further in, like the trainer's profile, pass `false` so Back still just goes back.
 * The back handler is registered only while the screen is focused, so it never swallows
 * back-presses on other screens.
 */
export function useStaffLogout({ confirmOnBack = true }: { confirmOnBack?: boolean } = {}) {
  const router = useRouter();
  const { adminLogout } = useAuth();
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (!confirmOnBack) return;
      const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
        setConfirmLogoutOpen(true);
        return true;
      });
      return () => subscription.remove();
    }, [confirmOnBack]),
  );

  const requestLogout = () => setConfirmLogoutOpen(true);

  const cancelLogout = () => setConfirmLogoutOpen(false);

  const confirmLogout = () => {
    setConfirmLogoutOpen(false);
    adminLogout();
    router.replace("/");
  };

  return { confirmLogoutOpen, requestLogout, cancelLogout, confirmLogout };
}
