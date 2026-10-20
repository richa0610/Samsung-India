import { afterAll, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";
import * as SecureStore from "expo-secure-store";

import { logoutAdmin } from "@/api/admin";
import { apiRequest } from "@/api/client";
import { AuthProvider, useAuth } from "@/hooks/useAuth";

const mockRouter = { replace: jest.fn(), push: jest.fn(), back: jest.fn() };

jest.mock("expo-router", () => ({ useRouter: () => mockRouter }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(async () => {}),
  deleteItemAsync: jest.fn(async () => {}),
}));
jest.mock("@/api/admin", () => ({ logoutAdmin: jest.fn(async () => null) }));
jest.mock("@/api/auth", () => ({ logoutTrainee: jest.fn(async () => null) }));
jest.mock("@/api/session", () => ({ clearCachedCurrentSession: jest.fn() }));
jest.mock("@/hooks/useCompany", () => ({ useBackfillCompany: () => {} }));
jest.mock("@/config/company", () => ({ getCompany: () => null }));
jest.mock("@/constants/api", () => ({ getApiBaseUrl: () => "http://server", getWsBaseUrl: () => "ws://server" }));

// The staff side keeps a live-events socket open; nothing here needs it to connect.
class FakeSocket {
  onopen: unknown = null;
  onmessage: unknown = null;
  onclose: unknown = null;
  onerror: unknown = null;
  send() {}
  close() {}
}
const realWebSocket = global.WebSocket;
const realFetch = global.fetch;
const mockFetch = jest.fn<typeof fetch>();
global.WebSocket = FakeSocket as unknown as typeof WebSocket;
global.fetch = mockFetch;

afterAll(() => {
  global.WebSocket = realWebSocket;
  global.fetch = realFetch;
});

const TRAINEE_KEY = "auth.session";
const STAFF_KEY = "auth.adminSession";
const saved: Record<string, string> = {};
const mockGetItem = jest.mocked(SecureStore.getItemAsync);

/** A token shaped like the server's, expiring `expiresIn` seconds from now. */
const token = (name: string, expiresIn: number) =>
  `header.${Buffer.from(JSON.stringify({ sub: name, exp: Math.floor(Date.now() / 1000) + expiresIn })).toString("base64url")}.signature`;
const staff = (access_token: string, role = "trainer") => ({ access_token, admin: { username: "someone", name: "Someone", role } });
const trainee = (access_token: string) => ({ access_token, trainee: { traineeUid: "TR-1", name: "Trainee" } });
const save = (key: string, session: object) => {
  saved[key] = JSON.stringify(session);
};

beforeEach(() => {
  jest.clearAllMocks();
  for (const key of Object.keys(saved)) delete saved[key];
  mockGetItem.mockImplementation(async (key: string) => saved[key] ?? null);
  mockFetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: "Invalid or expired session" }) } as Response);
});

async function openApp() {
  const { result } = await renderHook(() => useAuth(), { wrapper: AuthProvider });
  await waitFor(() => expect(result.current.restoring).toBe(false));
  return result;
}

/** A request made with `accessToken`, answered 401 by the server (see beforeEach). */
const requestWith = (accessToken: string) =>
  apiRequest("/admin/profile", { headers: { Authorization: `Bearer ${accessToken}` } }).catch(() => {});

test("a saved sign-in whose token has run out is forgotten, not restored", async () => {
  save(STAFF_KEY, staff(token("trainer1", -60)));
  save(TRAINEE_KEY, trainee(token("trainee1", -60)));
  const auth = await openApp();
  expect(auth.current.adminToken).toBeNull();
  expect(auth.current.token).toBeNull();
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(STAFF_KEY);
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(TRAINEE_KEY);
});

test("a saved sign-in that is still valid is restored", async () => {
  const current = token("trainer1", 3600);
  save(STAFF_KEY, staff(current));
  const auth = await openApp();
  expect(auth.current.adminToken).toBe(current);
  expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
});

test("a trainer's request answered 401 signs them out and opens the staff login, saying why", async () => {
  const current = token("trainer1", 3600);
  save(STAFF_KEY, staff(current));
  const auth = await openApp();

  await act(() => requestWith(current));

  await waitFor(() => expect(auth.current.adminToken).toBeNull());
  expect(mockRouter.replace).toHaveBeenCalledTimes(1);
  expect(mockRouter.replace).toHaveBeenCalledWith({ pathname: "/trainer_login", params: { reason: "session_expired" } });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(STAFF_KEY);
  expect(logoutAdmin).not.toHaveBeenCalled(); // the token is already dead - nothing to revoke
});

test("an admin lands on the admin wording of that screen", async () => {
  const current = token("boss", 3600);
  save(STAFF_KEY, staff(current, "admin"));
  await openApp();

  await act(() => requestWith(current));

  await waitFor(() =>
    expect(mockRouter.replace).toHaveBeenCalledWith({
      pathname: "/trainer_login",
      params: { reason: "session_expired", portal: "admin" },
    }),
  );
});

test("a trainee's request answered 401 opens the trainee login, saying why", async () => {
  const current = token("trainee1", 3600);
  save(TRAINEE_KEY, trainee(current));
  const auth = await openApp();

  await act(() => requestWith(current));

  await waitFor(() => expect(auth.current.token).toBeNull());
  expect(mockRouter.replace).toHaveBeenCalledWith({ pathname: "/participant_login", params: { reason: "session_expired" } });
  expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith(TRAINEE_KEY);
});

test("a late 401 for an older sign-in leaves the current one alone", async () => {
  const current = token("trainer1", 3600);
  save(STAFF_KEY, staff(current));
  const auth = await openApp();

  await act(() => requestWith(token("an-earlier-sign-in", 3600)));

  expect(auth.current.adminToken).toBe(current);
  expect(mockRouter.replace).not.toHaveBeenCalled();
});

test("several requests failing together sign out once", async () => {
  const current = token("trainer1", 3600);
  save(STAFF_KEY, staff(current));
  const auth = await openApp();

  await act(() => Promise.all([requestWith(current), requestWith(current), requestWith(current)]));

  await waitFor(() => expect(auth.current.adminToken).toBeNull());
  expect(mockRouter.replace).toHaveBeenCalledTimes(1);
});
