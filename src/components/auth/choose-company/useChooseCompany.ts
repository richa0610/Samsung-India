import { useRouter } from "expo-router";
import { useEffect, useState } from "react";

import { ApiError, chooseLoginCompany } from "@/api/admin";
import { useAuth } from "@/hooks/useAuth";
import { staffHome } from "@/hooks/useTrainerLogin";
import { getCompanyChoice, setCompanyChoice } from "@/services/companyChoice";

/** The choose-company page of an admin with access to several companies: the companies the staff
 *  login was answered with, and signing in to the one picked with its ticket. Opened without a
 *  pending choice (an app restart, a link) it goes back to the staff login. */
export function useChooseCompany() {
  const router = useRouter();
  const { setAdminSession } = useAuth();
  const [choice] = useState(getCompanyChoice);
  const [choosing, setChoosing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!choice) router.replace("/trainer_login");
  }, [choice, router]);

  const choose = async (tenantId: string) => {
    if (!choice || choosing) return;
    setChoosing(tenantId);
    setError(null);
    try {
      const session = await chooseLoginCompany(choice.ticket, tenantId);
      setCompanyChoice(null);
      setAdminSession(session);
      router.replace(staffHome(session.admin.role) ?? "/trainer_login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setChoosing(null);
    }
  };

  const back = () => {
    setCompanyChoice(null);
    router.replace({ pathname: "/trainer_login", params: { portal: "admin" } });
  };

  return { companies: choice?.companies ?? [], choose, choosing, error, back };
}
