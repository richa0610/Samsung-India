/**
 * useTrainerLogin Hook
 * Manages trainer/admin login form state, validations, authentication API, and role-based routing.
 */

import { useState } from "react";
import { useRouter } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, loginAdmin } from "@/api/admin";
import { cleanText } from "@/utils/validation";

export function useTrainerLogin(initialReason?: string) {
  const router = useRouter();
  const { setAdminSession } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState<string | null>(
    initialReason === "session_expired"
      ? "Your session expired. Please log in again."
      : null,
  );
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    const cleanUsername = cleanText(username, 10);
    if (!cleanUsername || !password) {
      setNotice("Enter your username and password.");
      return;
    }

    setLoading(true);
    setNotice(null);
    try {
      const session = await loginAdmin(cleanUsername, password);
      setAdminSession(session);
      if (session.admin.role === "admin") {
        router.replace("/admin_dashboard");
      } else if (session.admin.role === "trainer") {
        router.replace("/trainer_dashboard");
      } else {
        setNotice("This account doesn't have access here yet.");
      }
    } catch (err) {
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
