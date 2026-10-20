import { beforeEach, expect, jest, test } from "@jest/globals";
import { renderHook, waitFor } from "@testing-library/react-native";

import { fetchCurrentCompany } from "@/api/tenants";
import { Company, getCompany, setCompany } from "@/config/company";
import { useBackfillCompany } from "@/hooks/useCompany";

jest.mock("@/api/tenants", () => ({ fetchCurrentCompany: jest.fn() }));
jest.mock("@/config/company", () => ({
  getCompany: jest.fn(),
  setCompany: jest.fn(),
  subscribeCompany: () => () => {},
}));

const mockFetchCurrent = jest.mocked(fetchCurrentCompany);
const mockGetCompany = jest.mocked(getCompany);
const mockSetCompany = jest.mocked(setCompany);
const ACME: Company = { tenantId: "acme", companyName: "Acme Retail" };

beforeEach(() => {
  mockFetchCurrent.mockReset();
  mockFetchCurrent.mockResolvedValue(ACME);
  mockGetCompany.mockReset();
  mockGetCompany.mockReturnValue(null);
  mockSetCompany.mockReset();
});

test("a session from before company codes learns and saves its company", async () => {
  const { unmount } = await renderHook(() => useBackfillCompany("token", false));
  await waitFor(() => expect(mockSetCompany).toHaveBeenCalledWith(ACME));
  expect(mockFetchCurrent).toHaveBeenCalledWith("token");
  await unmount();
});

test("nothing is asked while signing in is unresolved, signed out, or when the company is known", async () => {
  for (const [token, restoring, company] of [
    ["token", true, null],
    [null, false, null],
    ["token", false, ACME],
  ] as const) {
    mockGetCompany.mockReturnValue(company);
    const { unmount } = await renderHook(() => useBackfillCompany(token, restoring));
    await unmount();
  }
  expect(mockFetchCurrent).not.toHaveBeenCalled();
});
