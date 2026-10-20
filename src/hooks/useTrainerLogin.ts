/**
 * useTrainerLogin Hook
 * Manages trainer/admin login form state, validations, authentication API, and role-based routing.
 */

import { useState } from "react";
import { useRouter } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, CompanyChoice, loginAdmin } from "@/api/admin";
import { signInNotice } from "@/constants/strings";
import { setCompanyChoice } from "@/services/companyChoice";
import { cleanText } from "@/utils/validation";

// A username, HO ID or phone number - as long as the field takes (StaffLoginScreen's maxLength).
const SIGN_IN_ID_MAX_LENGTH = 64;

/** Where a signed-in staff account lands, by the role the server gave it - null for any other role. */
export function staffHome(role: string): "/admin_dashboard" | "/trainer_dashboard" | null {
  if (role === "admin") return "/admin_dashboard";
  return role === "trainer" ? "/trainer_dashboard" : null;
}

function companyChoiceOf(err: unknown): CompanyChoice | null {
  const body = err instanceof ApiError && err.status === 409 ? (err.body as CompanyChoice | null) : null;
  return body?.code === "CHOOSE_COMPANY" ? body : null;
}

export function useTrainerLogin(initialReason?: string) {
  const router = useRouter();
  const { setAdminSession } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState<string | null>(signInNotice(initialReason));
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    const cleanUsername = cleanText(username, SIGN_IN_ID_MAX_LENGTH);
    if (!cleanUsername || !password) {
      setNotice("Enter your username and password.");
      return;
    }

    setLoading(true);
    setNotice(null);
    try {
      const session = await loginAdmin(cleanUsername, password);
      setAdminSession(session);
      const home = staffHome(session.admin.role);
      if (home) {
        router.replace(home);
      } else {
        setNotice("This account doesn't have access here yet.");
      }
    } catch (err) {
      // An admin with access to several companies picks one on its own page.
      const choice = companyChoiceOf(err);
      if (choice) {
        setCompanyChoice(choice);
        // A new route: in .expo/types once Metro regenerates them (the trainee login does the same).
        router.push("/choose_company" as any);
        return;
      }
      setNotice(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return {
    username,
    setUsername,
    password,
    setPassword,
    notice,
    loading,
    handleLogin,
  };
}
