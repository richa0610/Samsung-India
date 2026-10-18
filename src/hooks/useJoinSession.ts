import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";

import { ApiError } from "@/api/client";
import { SessionJoinInfo, getSessionJoinInfo, joinSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { useCompany } from "@/hooks/useCompany";
import { useLinkCompany } from "@/hooks/useLinkCompany";

/**
 * Drives `app/join/[code].tsx` - the screen a `samsungindia://join/<code>?company=<tenantId>`
 * deep link (from a scanned session QR) lands on.
 *
 * Fetches the public training preview - from the signed-in account's
 * company, or, signed out, from the company this device chose (the screen
 * asks for the company code first, or offers to switch to the company the
 * QR names - useLinkCompany; a QR code only opens in its own company) -
 * then on "Join": if the trainee is already signed in, binds them to the
 * session and goes to `/session`; otherwise hands off to the login screen
 * carrying the code so it can finish the bind after auth.
 */
export function useJoinSession() {
  const { code, company: linkTenant } = useLocalSearchParams<{ code: string; company?: string }>();
  const router = useRouter();
  const { token, restoring } = useAuth();
  const tenantId = useCompany()?.tenantId;
  const linkCompany = useLinkCompany(linkTenant ?? null, !!token, restoring);
  const sameCompany = linkCompany.state.kind === "same";

  const [info, setInfo] = useState<SessionJoinInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    // Not while the QR names another company: its code would be refused here.
    if (restoring || (!token && !tenantId) || !sameCompany) return;
    let active = true;
    // Each answer replaces the last one whole - after a company change, nothing of the previous
    // company's preview or error is left on screen.
    getSessionJoinInfo(code)
      .then((data) => {
        if (!active) return;
        setInfo(data);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setInfo(null);
        setError(err instanceof ApiError ? err.message : "Couldn't load this session.");
      });
    return () => {
      active = false;
    };
  }, [code, restoring, token, tenantId, sameCompany]);

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

  return {
    info,
    error,
    joining,
    // While the persisted session is still being read back (cold start from
    // the QR deep link is the common case), treat login status as unknown
    // rather than "logged out" - see useAuth's `restoring`.
    isLoggedIn: !!token,
    restoring,
    linkCompany: linkCompany.state,
    switchCompany: linkCompany.switchCompany,
    handleJoin,
    onBack: () => router.replace("/"),
  };
}
