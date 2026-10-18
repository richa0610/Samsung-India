import { afterAll, beforeEach, expect, jest, test } from "@jest/globals";

import { apiRequest, apiUpload } from "@/api/client";
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
});

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
