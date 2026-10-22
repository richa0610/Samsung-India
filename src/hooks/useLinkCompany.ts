import { useEffect, useState } from "react";

import { lookupCompany } from "@/api/tenants";
import { Company, setCompany } from "@/config/company";
import { useCompany } from "@/hooks/useCompany";

/** What the join screen does about the company a QR link names (`?company=<tenantId>`). */
export type LinkCompanyState =
  /** The company this phone already uses - carry on. */
  | { kind: "same" }
  /** No company in the link: a QR code made before they carried it (user, 2026-10-22). */
  | { kind: "out-of-date" }
  /** Asking the server about the link's company, then making it this phone's. */
  | { kind: "checking" }
  /** Signed in to another company: they must sign out first. */
  | { kind: "signed-in-elsewhere" }
  /** The link names a company the server doesn't know, or one that is suspended. */
  | { kind: "unknown" };

const sameTenant = (a: string, b: string | undefined) => !!b && a.trim().toLowerCase() === b.trim().toLowerCase();

/**
 * A QR code names the company its training belongs to (user, 2026-10-18). Signed out, the phone
 * takes that company once the server confirms it exists - whatever company it had, without asking
 * (user, 2026-10-22) - so the training's details show straight after the scan. The code is still
 * checked by the server against the company it is used in, and a sign-in from the QR admits only an
 * account of that company, so the link's company is only ever a hint.
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

  // Signed out: the QR's (confirmed) company becomes this phone's.
  useEffect(() => {
    if (!signedIn && !restoring && found?.company) setCompany(found.company);
  }, [signedIn, restoring, found]);

  let state: LinkCompanyState;
  if (!linkTenant) state = { kind: "out-of-date" };
  else if (!differs || restoring) state = { kind: "same" };
  // Signed in with no company saved yet (a session from before company codes): the server decides.
  else if (signedIn) state = saved ? { kind: "signed-in-elsewhere" } : { kind: "same" };
  else if (found && !found.company) state = { kind: "unknown" };
  else state = { kind: "checking" };

  return { state };
}
