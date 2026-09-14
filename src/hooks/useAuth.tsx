import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

import { AdminAccount, AdminAuthSession } from "@/api/admin";
import { AuthSession, Trainee } from "@/api/auth";
import { getWsBaseUrl } from "@/constants/api";
import { USE_MOCK_DATA } from "@/config/dataSource";
import { DEMO_AUTH_SESSION } from "@/data/mockData";
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
  const [session, setSessionState] = useState<AuthSession | null>(INITIAL_SESSION);
  const [adminSession, setAdminSessionState] = useState<AdminAuthSession | null>(null);
  const [restoring, setRestoring] = useState(!USE_MOCK_DATA && CAN_PERSIST);
  const adminToken = adminSession?.access_token ?? null;

  // One-shot rehydration on mount. Mock data already starts "logged in" via
  // INITIAL_SESSION, and there's nothing to read back on web.
  useEffect(() => {
    if (USE_MOCK_DATA || !CAN_PERSIST) return;
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
  }, []);

  const logout = useCallback(() => {
    setSessionState(null);
    writeStored(AUTH_SESSION_KEY, null);
  }, []);

  const setAdminSession = useCallback((next: AdminAuthSession) => {
    setAdminSessionState(next);
    writeStored(ADMIN_SESSION_KEY, next);
  }, []);

  const adminLogout = useCallback(() => {
    setAdminSessionState(null);
    writeStored(ADMIN_SESSION_KEY, null);
  }, []);

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
