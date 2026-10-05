import { useCallback, useEffect, useState } from "react";

import { fetchJoinLink } from "@/api/training";
import { useAuth } from "@/hooks/useAuth";

/** The signed join link for a training's QR code, fetched while `enabled` (the QR modal is open).
 *  `link` is null until it arrives; `failed` offers a retry. */
export function useJoinLink(conferenceUid: string, enabled: boolean) {
  const { adminToken } = useAuth();
  const [state, setState] = useState<{ uid: string; link: string | null; failed: boolean }>({
    uid: conferenceUid,
    link: null,
    failed: false,
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!enabled || !adminToken || !conferenceUid) return;
    let active = true;
    fetchJoinLink(adminToken, conferenceUid)
      .then((link) => {
        if (active) setState({ uid: conferenceUid, link, failed: false });
      })
      .catch(() => {
        if (active) setState({ uid: conferenceUid, link: null, failed: true });
      });
    return () => {
      active = false;
    };
  }, [enabled, adminToken, conferenceUid, attempt]);

  // A link fetched for another training never shows for this one.
  const current = state.uid === conferenceUid ? state : { link: null, failed: false };
  const retry = useCallback(() => {
    setState({ uid: conferenceUid, link: null, failed: false });
    setAttempt((n) => n + 1);
  }, [conferenceUid]);

  return { link: current.link, loading: enabled && !current.link && !current.failed, failed: current.failed, retry };
}
