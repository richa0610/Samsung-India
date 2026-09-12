import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";

import { ApiError } from "@/api/client";
import { SessionJoinInfo, getSessionJoinInfo, joinSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";

/**
 * Drives `app/join/[code].tsx` - the screen a `samsungindia://join/<code>`
 * deep link (from a scanned session QR) lands on.
 *
 * Fetches the public training preview, then on "Join": if the trainee is
 * already signed in, binds them to the session and goes to `/session`;
 * otherwise hands off to the login screen carrying the code so it can
 * finish the bind after auth.
 */
export function useJoinSession() {
  const { code } = useLocalSearchParams<{ code: string }>();
  const router = useRouter();
  const { token } = useAuth();

  const [info, setInfo] = useState<SessionJoinInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    let active = true;
    getSessionJoinInfo(code)
      .then((data) => {
        if (active) setInfo(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof ApiError ? err.message : "Couldn't load this session.");
      });
    return () => {
      active = false;
    };
  }, [code]);

  const handleJoin = async () => {
    if (!token) {
      router.replace({ pathname: "/participant_login", params: { join: code } });
      return;
    }
    setJoining(true);
    setError(null);
    try {
      await joinSession(code, token);
      router.replace("/session");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't join this session.");
      setJoining(false);
    }
  };

  return { info, error, joining, isLoggedIn: !!token, handleJoin, onBack: () => router.replace("/") };
}
