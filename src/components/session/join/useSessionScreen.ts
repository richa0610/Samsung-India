import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";

import { CurrentSession, getCurrentSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { traineeAvatar } from "@/utils/traineeAvatar";

export function useSessionScreen() {
  const router = useRouter();
  const { trainee, token, logout } = useAuth();
  const avatar = traineeAvatar(trainee, token);

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
    // replace (not push): every other transition into and out of this
    // screen already uses replace, so nothing stale sits underneath it in
    // the stack - a push here was the one gap, leaving this "waiting for
    // the trainer" screen sitting under Home. Every trainee tab
    // (Home/Dashboard/Rank/Profile) already replaces the others in place,
    // so hardware back from any of them was popping down into this now
    // long-since-stale screen, which renders blank once a session's
    // actually in progress.
    router.replace({ pathname: "/session_detail" });
  };

  return { trainee, avatar, loading, notice, details, handleLogout, handleJoinSession };
}
