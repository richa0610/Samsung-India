import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { ApiError } from "@/api/client";
import { lookupCompany } from "@/api/tenants";
import { Company, setCompany } from "@/config/company";
import { useLinkCompany } from "@/hooks/useLinkCompany";

let mockCompany: Company | null = null;

jest.mock("@/hooks/useCompany", () => ({ useCompany: () => mockCompany }));
jest.mock("@/api/tenants", () => ({ lookupCompany: jest.fn() }));
jest.mock("@/config/company", () => ({ setCompany: jest.fn() }));

const mockLookup = jest.mocked(lookupCompany);
const mockSetCompany = jest.mocked(setCompany);
const SAMSUNG: Company = { tenantId: "samsung", companyName: "Samsung India" };
const DEMO: Company = { tenantId: "demo", companyName: "DEMO Bharat Electronics Pvt Ltd" };

beforeEach(() => {
  mockCompany = SAMSUNG;
  mockLookup.mockReset();
  mockLookup.mockResolvedValue(DEMO);
  mockSetCompany.mockReset();
});

test("a link naming this phone's company - in any letter case - or no company carries on", async () => {
  for (const link of [null, "samsung", "SAMSUNG"]) {
    const { result, unmount } = await renderHook(() => useLinkCompany(link, false, false));
    expect(result.current.state).toEqual({ kind: "same" });
    await unmount();
  }
  expect(mockLookup).not.toHaveBeenCalled();
});

test("signed out on another company: the person is asked, and only switching changes it", async () => {
  // (While the server is asked the state is "checking" - see useJoinSession.test.ts.)
  const { result, unmount } = await renderHook(() => useLinkCompany("demo", false, false));
  await waitFor(() => expect(result.current.state).toEqual({ kind: "switch", company: DEMO }));
  expect(mockSetCompany).not.toHaveBeenCalled();

  await act(() => result.current.switchCompany());
  expect(mockSetCompany).toHaveBeenCalledWith(DEMO);
  await unmount();
});

test("a phone with no company yet takes the QR's, once the server confirms it", async () => {
  mockCompany = null;
  const { unmount } = await renderHook(() => useLinkCompany("demo", false, false));
  await waitFor(() => expect(mockSetCompany).toHaveBeenCalledWith(DEMO));
  await unmount();
});

test("a company the server doesn't know is never saved", async () => {
  mockCompany = null;
  mockLookup.mockRejectedValue(new ApiError("Company code not found", 404));
  const { result, unmount } = await renderHook(() => useLinkCompany("nope", false, false));
  await waitFor(() => expect(result.current.state).toEqual({ kind: "unknown" }));
  expect(mockSetCompany).not.toHaveBeenCalled();
  await unmount();
});

test("signed in to another company: sign out first - nothing is looked up or switched", async () => {
  const { result, unmount } = await renderHook(() => useLinkCompany("demo", true, false));
  expect(result.current.state).toEqual({ kind: "signed-in-elsewhere" });
  await act(() => result.current.switchCompany());
  expect(mockLookup).not.toHaveBeenCalled();
  expect(mockSetCompany).not.toHaveBeenCalled();
  await unmount();
});
