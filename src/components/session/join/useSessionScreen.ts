import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";

import { CurrentSession, getCurrentSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { traineeAvatar } from "@/utils/traineeAvatar";

export function useSessionScreen() {
  const router = useRouter();
  const { trainee, token, logout } = useAuth();
  const avatar = traineeAvatar(trainee);

  const [session, setSession] = useState<CurrentSession | null>(null);
  const [loading, setLoading] = useState(true);

  const details: [string, string][] = [
    ["SUPERVISOR", trainee?.supervisorName || "N/A"],
    ["DESIGNATION", trainee?.designation || "N/A"],
    ["DISTRICT", trainee?.district || "N/A"],
    ["COMPANY ID", trainee?.employee_id || "N/A"],
  ];

  const loadSession = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await getCurrentSession(token);
      setSession(data);
    } catch {
      // No trainer session assigned yet (e.g. 404) - fall back to the
      // "not assigned" notice below instead of surfacing an error.
      setSession(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Re-check every time this screen regains focus so a session that just
  // got approved/started shows up without needing to log out and back in.
  useFocusEffect(
    useCallback(() => {
      loadSession();
    }, [loadSession]),
  );

  const notice = !session
    ? "You are registered but not assigned to this session"
    : !session.started
      ? `Session with ${session.trainerName || "your trainer"} starts ${session.startsAt || "soon"}`
      : `Session with ${session.trainerName || "your trainer"} is live now`;

  const handleLogout = () => {
    logout();
    router.back();
  };

  const handleJoinSession = () => {
    // Admission is now trainer-controlled: the trainee just enters the
    // session screen, which shows the "waiting for the trainer" card until
    // the trainer marks them present, then reveals the module timeline.
    router.push({ pathname: "/session_detail" });
  };

  return { trainee, avatar, loading, notice, details, handleLogout, handleJoinSession };
}
