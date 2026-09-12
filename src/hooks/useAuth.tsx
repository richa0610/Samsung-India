import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { AdminAccount, AdminAuthSession } from "@/api/admin";
import { AuthSession, Trainee } from "@/api/auth";
import { getWsBaseUrl } from "@/constants/api";
import { USE_MOCK_DATA } from "@/config/dataSource";
import { DEMO_AUTH_SESSION } from "@/data/mockData";
import { emit } from "@/services/liveEvents";

// How long to wait before retrying a dropped /ws/admin connection - mobile
// networks blip often, and a single fixed delay is plenty for this app's
// scale (no exponential backoff needed).
const WS_RECONNECT_DELAY_MS = 3000;

// On mock data, start already "logged in" as the demo trainee so screens
// like /session show real values without requiring a register/login round-trip.
const INITIAL_SESSION: AuthSession | null = USE_MOCK_DATA
  ? (DEMO_AUTH_SESSION as AuthSession)
  : null;

type AuthContextValue = {
  trainee: Trainee | null;
  token: string | null;
  isAuthenticated: boolean;
  setSession: (session: AuthSession) => void;
  logout: () => void;

  admin: AdminAccount | null;
  adminToken: string | null;
  isAdminAuthenticated: boolean;
  setAdminSession: (session: AdminAuthSession) => void;
  adminLogout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<AuthSession | null>(INITIAL_SESSION);
  const [adminSession, setAdminSessionState] = useState<AdminAuthSession | null>(null);
  const adminToken = adminSession?.access_token ?? null;

  // Persistent live-events connection for the trainer/admin side (new
  // training / new trainee / confirmed attendance pushes) - lives here so
  // it survives screen navigation instead of reconnecting per-screen, and
  // its lifecycle just follows adminToken (open on login, close on logout).
  useEffect(() => {
    if (USE_MOCK_DATA || !adminToken) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const connect = () => {
      socket = new WebSocket(`${getWsBaseUrl()}/ws/admin?token=${adminToken}`);
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string);
          if (data?.type) emit(data);
        } catch {
          // Ignore malformed pushes rather than crashing the socket handler.
        }
      };
      socket.onclose = () => {
        if (!stopped) reconnectTimer = setTimeout(connect, WS_RECONNECT_DELAY_MS);
      };
      socket.onerror = () => socket?.close();
    };
    connect();

    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [adminToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      trainee: session?.trainee ?? null,
      token: session?.access_token ?? null,
      isAuthenticated: !!session,
      setSession: setSessionState,
      logout: () => setSessionState(null),

      admin: adminSession?.admin ?? null,
      adminToken,
      isAdminAuthenticated: !!adminSession,
      setAdminSession: setAdminSessionState,
      adminLogout: () => setAdminSessionState(null),
    }),
    [session, adminSession, adminToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
