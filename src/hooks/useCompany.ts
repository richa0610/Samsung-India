import { useEffect, useSyncExternalStore } from "react";

import { fetchCurrentCompany } from "@/api/tenants";
import { Company, getCompany, setCompany, subscribeCompany } from "@/config/company";

/** The company this device signs in to (src/config/company.ts), re-rendering when it changes. */
export function useCompany(): Company | null {
  return useSyncExternalStore(subscribeCompany, getCompany, getCompany);
}

/**
 * A device signed in before company codes existed has a session but no saved company: ask the
 * server which company that session's token belongs to and save it, so the person isn't asked for
 * a code after they sign out, and screens that show the company have it. Best-effort - a failure
 * leaves things as they are until the next launch.
 */
export function useBackfillCompany(token: string | null, restoring: boolean): void {
  useEffect(() => {
    if (restoring || !token || getCompany()) return;
    let active = true;
    fetchCurrentCompany(token)
      .then((company) => {
        if (active && !getCompany()) setCompany(company);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [token, restoring]);
}
