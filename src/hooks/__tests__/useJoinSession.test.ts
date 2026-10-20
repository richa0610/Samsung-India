import { beforeEach, expect, jest, test } from "@jest/globals";
import { renderHook, waitFor } from "@testing-library/react-native";

import { getSessionJoinInfo } from "@/api/session";
import { Company } from "@/config/company";
import { useJoinSession } from "@/hooks/useJoinSession";

let mockAuth: { token: string | null; restoring: boolean } = { token: null, restoring: false };
let mockCompany: Company | null = null;
let mockParams: { code: string; company?: string } = { code: "CONF2600001.SIG" };

jest.mock("expo-router", () => ({
  useLocalSearchParams: () => mockParams,
  useRouter: () => ({ replace: jest.fn() }),
}));
jest.mock("@/api/tenants", () => ({ lookupCompany: jest.fn(() => new Promise(() => {})) }));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => mockAuth }));
jest.mock("@/hooks/useCompany", () => ({ useCompany: () => mockCompany }));
jest.mock("@/api/session", () => ({ getSessionJoinInfo: jest.fn(), joinSession: jest.fn() }));

const mockJoinInfo = jest.mocked(getSessionJoinInfo);

beforeEach(() => {
  mockAuth = { token: null, restoring: false };
  mockCompany = null;
  mockParams = { code: "CONF2600001.SIG" };
  mockJoinInfo.mockReset();
  mockJoinInfo.mockResolvedValue({ title: "Training" } as Awaited<ReturnType<typeof getSessionJoinInfo>>);
});

test("signed out, the preview waits for the company code - a QR code opens only in its company", async () => {
  const { unmount } = await renderHook(() => useJoinSession());
  expect(mockJoinInfo).not.toHaveBeenCalled();
  await unmount();
});

test("signed out with a company, the preview loads", async () => {
  mockCompany = { tenantId: "acme", companyName: "Acme Retail" };
  const { result, unmount } = await renderHook(() => useJoinSession());
  await waitFor(() => expect(result.current.info).toEqual({ title: "Training" }));
  expect(mockJoinInfo).toHaveBeenCalledWith("CONF2600001.SIG");
  await unmount();
});

test("signed in, the preview loads from the account's own company", async () => {
  mockAuth = { token: "token", restoring: false };
  const { unmount } = await renderHook(() => useJoinSession());
  await waitFor(() => expect(mockJoinInfo).toHaveBeenCalled());
  await unmount();
});

test("a QR naming another company loads nothing until the phone is on that company", async () => {
  mockCompany = { tenantId: "acme", companyName: "Acme Retail" };
  mockParams = { code: "CONF2600001.SIG", company: "demo" };
  const { result, unmount } = await renderHook(() => useJoinSession());
  expect(result.current.linkCompany.kind).toBe("checking");
  expect(mockJoinInfo).not.toHaveBeenCalled();
  await unmount();
});

test("a QR naming this phone's own company loads as usual", async () => {
  mockCompany = { tenantId: "acme", companyName: "Acme Retail" };
  mockParams = { code: "CONF2600001.SIG", company: "ACME" };
  const { unmount } = await renderHook(() => useJoinSession());
  await waitFor(() => expect(mockJoinInfo).toHaveBeenCalled());
  await unmount();
});

test("nothing loads while the saved sign-in is still being read", async () => {
  mockAuth = { token: null, restoring: true };
  mockCompany = { tenantId: "acme", companyName: "Acme Retail" };
  const { unmount } = await renderHook(() => useJoinSession());
  expect(mockJoinInfo).not.toHaveBeenCalled();
  await unmount();
});
