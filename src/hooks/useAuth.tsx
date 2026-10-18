import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

import { AdminAccount, AdminAuthSession, logoutAdmin } from "@/api/admin";
import { AuthSession, Trainee, logoutTrainee } from "@/api/auth";
import { clearCachedCurrentSession } from "@/api/session";
import { getWsBaseUrl } from "@/constants/api";
import { useBackfillCompany } from "@/hooks/useCompany";
import { emit } from "@/services/liveEvents";

// Cold-start persistence for both sessions - without this, a still-valid JWT
// was lost the instant the app process died (backgrounded + killed by the
// OS, or a fresh launch from a scanned QR deep link), forcing a re-login
// even though the token itself hadn't expired. SecureStore has no web
// implementation, so persistence is native-only; web keeps the old
// in-memory-only behaviour.
const AUTH_SESSION_KEY = "auth.session";
const ADMIN_SESSION_KEY = "auth.adminSession";
const CAN_PERSIST = Platform.OS !== "web";

async function readStored<T>(key: string): Promise<T | null> {
  if (!CAN_PERSIST) return null;
  try {
    const raw = await SecureStore.getItemAsync(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function writeStored(key: string, value: unknown | null) {
  if (!CAN_PERSIST) return;
  if (value == null) {
    SecureStore.deleteItemAsync(key).catch(() => {});
  } else {
    SecureStore.setItemAsync(key, JSON.stringify(value)).catch(() => {});
  }
}

// How long to wait before retrying a dropped /ws/admin connection - mobile
// networks blip often, and a single fixed delay is plenty for this app's
// scale (no exponential backoff needed).
const WS_RECONNECT_DELAY_MS = 3000;

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
  updateAdminPhoto: (profilePicture: string) => void;
  adminLogout: () => void;

  // True until the persisted session(s) have been read back from disk on
  // app launch - callers that redirect to a login screen the instant
  // token/adminToken looks empty (e.g. the QR-join flow) should wait for
  // this to go false first, or they'll bounce an already-logged-in user.
  restoring: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<AuthSession | null>(null);
  const [adminSession, setAdminSessionState] = useState<AdminAuthSession | null>(null);
  const [restoring, setRestoring] = useState(CAN_PERSIST);
  const adminToken = adminSession?.access_token ?? null;
  useBackfillCompany(session?.access_token ?? adminToken, restoring);

  // One-shot rehydration on mount - there's nothing to read back on web.
  useEffect(() => {
    if (!CAN_PERSIST) return;
    let active = true;
    Promise.all([readStored<AuthSession>(AUTH_SESSION_KEY), readStored<AdminAuthSession>(ADMIN_SESSION_KEY)]).then(
      ([storedSession, storedAdminSession]) => {
        if (!active) return;
        if (storedSession) setSessionState(storedSession);
        if (storedAdminSession) setAdminSessionState(storedAdminSession);
        setRestoring(false);
      },
    );
    return () => {
      active = false;
    };
  }, []);

  const setSession = useCallback((next: AuthSession) => {
    setSessionState(next);
    writeStored(AUTH_SESSION_KEY, next);
    setAdminSessionState(null);
    writeStored(ADMIN_SESSION_KEY, null);
  }, []);

  const logout = useCallback(() => {
    // Revoke the token server-side too; best-effort - signing out locally never waits on it.
    if (session?.access_token) logoutTrainee(session.access_token).catch(() => {});
    clearCachedCurrentSession();
    setSessionState(null);
    writeStored(AUTH_SESSION_KEY, null);
  }, [session]);

  const setAdminSession = useCallback((next: AdminAuthSession) => {
    setAdminSessionState(next);
    writeStored(ADMIN_SESSION_KEY, next);
    setSessionState(null);
    writeStored(AUTH_SESSION_KEY, null);
  }, []);

  const adminLogout = useCallback(() => {
    // Revoke the token server-side too; best-effort - signing out locally never waits on it.
    if (adminSession?.access_token) logoutAdmin(adminSession.access_token).catch(() => {});
    setAdminSessionState(null);
    writeStored(ADMIN_SESSION_KEY, null);
  }, [adminSession]);

  const updateAdminPhoto = useCallback((profilePicture: string) => {
    setAdminSessionState((current) => {
      if (!current) return current;
      const next = { ...current, admin: { ...current.admin, profilePicture } };
      writeStored(ADMIN_SESSION_KEY, next);
      return next;
    });
  }, []);

  // Persistent live-events connection for the trainer/admin side (new
  // training / new trainee / confirmed attendance pushes) - lives here so
  // it survives screen navigation instead of reconnecting per-screen, and
  // its lifecycle just follows adminToken (open on login, close on logout).
  useEffect(() => {
    if (!adminToken) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const connect = () => {
      // The token goes in the first message, never the URL - URLs end up in proxy access logs.
      const ws = new WebSocket(`${getWsBaseUrl()}/ws/admin`);
      ws.onopen = () => ws.send(JSON.stringify({ type: "auth", token: adminToken }));
      socket = ws;
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
      setSession,
      logout,

      admin: adminSession?.admin ?? null,
      adminToken,
      isAdminAuthenticated: !!adminSession,
      setAdminSession,
      // Lets a successful photo upload (useTrainerProfileForm) update the
      // avatar shown everywhere else in the trainer flow (dashboard header,
      // etc.) immediately, without a full re-login just to refresh one field.
      updateAdminPhoto,
      adminLogout,

      restoring,
    }),
    [session, adminSession, adminToken, restoring, setSession, logout, setAdminSession, updateAdminPhoto, adminLogout]
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
