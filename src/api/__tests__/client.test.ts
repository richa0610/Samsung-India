import { afterAll, beforeEach, expect, jest, test } from "@jest/globals";

import { apiRequest, apiUpload, setSessionEndedHandler } from "@/api/client";
import { Company, getCompany } from "@/config/company";

jest.mock("@/config/company", () => ({ getCompany: jest.fn() }));
jest.mock("@/constants/api", () => ({ getApiBaseUrl: () => "http://server" }));

const mockGetCompany = jest.mocked(getCompany);
const ACME: Company = { tenantId: "acme", companyName: "Acme Retail" };
const realFetch = global.fetch;
const mockFetch = jest.fn<typeof fetch>();
global.fetch = mockFetch;

afterAll(() => {
  global.fetch = realFetch;
});

beforeEach(() => {
  mockFetch.mockReset();
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({}) } as Response);
  mockGetCompany.mockReset();
  setSessionEndedHandler(null);
});

const answer = (status: number, detail: string) =>
  mockFetch.mockResolvedValue({ ok: false, status, json: async () => ({ detail }) } as Response);

const sentHeaders = () => (mockFetch.mock.calls[0][1] as RequestInit).headers as Record<string, string>;

test("every request names the device's company, so the server signs people in to it", async () => {
  mockGetCompany.mockReturnValue(ACME);
  await apiRequest("/trainees/login", { method: "POST", headers: { Authorization: "Bearer t" } });
  expect(sentHeaders()).toEqual({ "Content-Type": "application/json", "X-Tenant-ID": "acme", Authorization: "Bearer t" });
});

test("uploads name it too", async () => {
  mockGetCompany.mockReturnValue(ACME);
  await apiUpload("/trainees/me/photo", new FormData(), "t");
  expect(sentHeaders()).toEqual({ "X-Tenant-ID": "acme", Authorization: "Bearer t" });
});

test("no company chosen yet: no company header", async () => {
  mockGetCompany.mockReturnValue(null);
  await apiRequest("/tenants/lookup?code=acme");
  expect(sentHeaders()).not.toHaveProperty("X-Tenant-ID");
});

test("a signed-in request answered 401 reports that sign-in as ended, and still fails", async () => {
  const ended = jest.fn();
  setSessionEndedHandler(ended);
  answer(401, "Invalid or expired session");
  await expect(apiRequest("/admin/profile", { headers: { Authorization: "Bearer old-token" } })).rejects.toMatchObject({
    status: 401,
    message: "Invalid or expired session",
  });
  expect(ended).toHaveBeenCalledWith("old-token", undefined);   // no code: an ordinary expired session
});

test("an upload answered 401 reports it too", async () => {
  const ended = jest.fn();
  setSessionEndedHandler(ended);
  answer(401, "Invalid or expired session");
  await expect(apiUpload("/trainees/me/photo", new FormData(), "old-token")).rejects.toMatchObject({ status: 401 });
  expect(ended).toHaveBeenCalledWith("old-token", undefined);   // no code: an ordinary expired session
});

test("a wrong password at login is not a sign-in ending - a login carries no token", async () => {
  const ended = jest.fn();
  setSessionEndedHandler(ended);
  answer(401, "Invalid username or password");
  await expect(apiRequest("/admin/login", { method: "POST" })).rejects.toMatchObject({ status: 401 });
  expect(ended).not.toHaveBeenCalled();
});

test("a sign-out by a sign-in on another device passes the server's code on", async () => {
  const ended = jest.fn();
  setSessionEndedHandler(ended);
  mockFetch.mockResolvedValue({
    ok: false,
    status: 401,
    json: async () => ({ detail: { code: "SIGNED_IN_ELSEWHERE", message: "Signed in elsewhere" } }),
  } as Response);
  await expect(apiRequest("/admin/profile", { headers: { Authorization: "Bearer t" } })).rejects.toMatchObject({
    status: 401,
    message: "Signed in elsewhere",
  });
  expect(ended).toHaveBeenCalledWith("t", "SIGNED_IN_ELSEWHERE");
});

test("a request that names no company leaves the phone's company out", async () => {
  mockGetCompany.mockReturnValue(ACME);
  await apiRequest("/trainees/login", { method: "POST" }, { company: false });
  expect(sentHeaders()).not.toHaveProperty("X-Tenant-ID");
});

test("any other refusal of a signed-in request is not either", async () => {
  const ended = jest.fn();
  setSessionEndedHandler(ended);
  answer(403, "Not authorized for this tenant");
  await expect(apiRequest("/admin/dashboard/stats", { headers: { Authorization: "Bearer t" } })).rejects.toMatchObject({
    status: 403,
  });
  expect(ended).not.toHaveBeenCalled();
});
