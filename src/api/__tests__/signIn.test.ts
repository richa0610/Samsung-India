import { afterAll, beforeEach, expect, jest, test } from "@jest/globals";

import { chooseLoginCompany, loginAdmin } from "@/api/admin";
import { loginTrainee, registerTrainee } from "@/api/auth";
import { getCompany } from "@/config/company";

// Sign-in names no company (user, 2026-10-19) - the server finds it - and names this device, which
// counts toward the person's device limit. Registering still goes to the phone's company.
jest.mock("@/config/company", () => ({ getCompany: jest.fn() }));
jest.mock("@/config/device", () => ({ getDeviceId: () => "device-1", getDeviceName: () => "Pixel 8 (Android)" }));
jest.mock("@/constants/api", () => ({ getApiBaseUrl: () => "http://server" }));

const realFetch = global.fetch;
const mockFetch = jest.fn<typeof fetch>();
global.fetch = mockFetch;
afterAll(() => {
  global.fetch = realFetch;
});

beforeEach(() => {
  mockFetch.mockReset();
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({}) } as Response);
  // An old company saved on this phone - sign-in must not send it.
  jest.mocked(getCompany).mockReturnValue({ tenantId: "old-co", companyName: "Old Co" });
});

const sent = () => {
  const init = mockFetch.mock.calls[0][1] as RequestInit;
  return { headers: init.headers as Record<string, string>, body: JSON.parse(init.body as string) };
};

test("a trainee signs in with this device and no company code", async () => {
  await loginTrainee("DEMO-EMP-001", "secret");
  expect(sent().body).toEqual({ identifier: "DEMO-EMP-001", password: "secret", deviceId: "device-1", deviceName: "Pixel 8 (Android)" });
  expect(sent().headers).not.toHaveProperty("X-Tenant-ID");
});

test("staff sign in the same way", async () => {
  await loginAdmin("trainer1", "secret");
  expect(sent().body).toEqual({ username: "trainer1", password: "secret", deviceId: "device-1", deviceName: "Pixel 8 (Android)" });
  expect(sent().headers).not.toHaveProperty("X-Tenant-ID");
});

test("an admin's company choice sends the ticket and the company picked", async () => {
  await chooseLoginCompany("a-ticket", "demo");
  expect(sent().body).toEqual({ ticket: "a-ticket", tenantId: "demo" });
  expect(mockFetch.mock.calls[0][0]).toBe("http://server/admin/login/company");
});

test("registering goes to the phone's company, on this device", async () => {
  await registerTrainee({ name: "New", phone: "9876543210", email: "n@example.com", state: "Delhi" });
  expect(sent().headers["X-Tenant-ID"]).toBe("old-co");
  expect(sent().body).toMatchObject({ phone: 9876543210, deviceId: "device-1", deviceName: "Pixel 8 (Android)" });
});
