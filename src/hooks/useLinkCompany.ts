import { useEffect, useState } from "react";

import { lookupCompany } from "@/api/tenants";
import { Company, setCompany } from "@/config/company";
import { useCompany } from "@/hooks/useCompany";

/** What the join screen does about the company a QR link names (`?company=<tenantId>`). */
export type LinkCompanyState =
  /** No company in the link, or the one this phone already uses - carry on. */
  | { kind: "same" }
  /** Asking the server about the link's company (or saving it as this phone's first company). */
  | { kind: "checking" }
  /** Signed out, this phone is set to another company: ask before switching. */
  | { kind: "switch"; company: Company }
  /** Signed in to another company: they must sign out first. */
  | { kind: "signed-in-elsewhere" }
  /** The link names a company the server doesn't know, or one that is suspended. */
  | { kind: "unknown" };

const sameTenant = (a: string, b: string | undefined) => !!b && a.trim().toLowerCase() === b.trim().toLowerCase();

/**
 * A QR code names the company its training belongs to (user, 2026-10-18), so a phone set to another
 * company can switch instead of failing with "invalid code". A phone with no company yet simply
 * takes the QR's company once the server confirms it exists - the code is still checked by the
 * server against the company it is used in, so the link's company is only ever a hint.
 */
export function useLinkCompany(linkTenant: string | null, signedIn: boolean, restoring: boolean) {
  const saved = useCompany();
  const differs = !!linkTenant && !sameTenant(linkTenant, saved?.tenantId);
  const [lookup, setLookup] = useState<{ tenant: string; company: Company | null } | null>(null);

  useEffect(() => {
    if (!linkTenant || !differs || signedIn || restoring) return;
    let active = true;
    lookupCompany(linkTenant)
      .then((company) => {
        if (active) setLookup({ tenant: linkTenant, company });
      })
      .catch(() => {
        if (active) setLookup({ tenant: linkTenant, company: null });
      });
    return () => {
      active = false;
    };
  }, [linkTenant, differs, signedIn, restoring]);

  const found = lookup && lookup.tenant === linkTenant ? lookup : null;

  // No company on this phone yet: the QR's (confirmed) company becomes it.
  useEffect(() => {
    if (!signedIn && !restoring && !saved && found?.company) setCompany(found.company);
  }, [signedIn, restoring, saved, found]);

  let state: LinkCompanyState;
  if (!differs || restoring) state = { kind: "same" };
  // Signed in with no company saved yet (a session from before company codes): the server decides.
  else if (signedIn) state = saved ? { kind: "signed-in-elsewhere" } : { kind: "same" };
  else if (!found) state = { kind: "checking" };
  else if (!found.company) state = { kind: "unknown" };
  else if (!saved) state = { kind: "checking" };
  else state = { kind: "switch", company: found.company };

  const switchCompany = () => {
    if (state.kind === "switch") setCompany(state.company);
  };

  return { state, switchCompany };
}
