import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchTrainingFacets, fetchTrainingsPage } from "@/api/training";
import { useSessionsScreen } from "../useSessionsScreen";

let mockParams: Record<string, string> = {};

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
  useLocalSearchParams: () => mockParams,
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "trainer-token" }) }));
jest.mock("@/api/training", () => ({ fetchTrainingsPage: jest.fn(), fetchTrainingFacets: jest.fn() }));

const mockPage = jest.mocked(fetchTrainingsPage);
const mockFacets = jest.mocked(fetchTrainingFacets);
const pageOf = (page: number) =>
  ({ items: [{ conferenceUid: `C${page}` }], total: 60, page, pageSize: 20, totalPages: 3, nextCursor: null }) as never;

beforeEach(() => {
  mockParams = {};
  mockPage.mockReset();
  mockFacets.mockReset();
  mockFacets.mockResolvedValue({ trainingHubs: [], trainingTypes: [] });
});
afterEach(() => {
  jest.useRealTimers();
});

test("two end-of-list events at once load the next page once", async () => {
  mockPage.mockImplementation(async (_token, options) => pageOf(options.page ?? 1));
  const { result } = await renderHook(() => useSessionsScreen());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(async () => {
    await Promise.all([result.current.loadMore(), result.current.loadMore()]);
  });
  expect(mockPage.mock.calls.filter(([, options]) => options.page === 2)).toHaveLength(1);
  expect(result.current.filteredSessions.map((s) => s.conferenceUid)).toEqual(["C1", "C2"]);
});

test("the Today tab asks for today's date in India", async () => {
  jest.useFakeTimers({ now: new Date("2026-09-29T19:00:00Z"), doNotFake: ["setTimeout", "setInterval", "clearTimeout", "clearInterval"] });
  mockPage.mockImplementation(async (_token, options) => pageOf(options.page ?? 1));
  const { result } = await renderHook(() => useSessionsScreen());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(() => result.current.setActiveTab("today"));
  await waitFor(() => expect(mockPage.mock.calls.at(-1)?.[1]).toMatchObject({ onDate: "2026-09-30" })); // 00:30 IST
});

test("the Ongoing card lists every running training, whatever the date", async () => {
  mockParams = { tab: "all", status: "ongoing" };
  mockPage.mockImplementation(async (_token, options) => pageOf(options.page ?? 1));
  const { result } = await renderHook(() => useSessionsScreen());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(mockPage.mock.calls.at(-1)?.[1]).toMatchObject({ status: "ongoing", filters: { start: "", end: "" } });
  expect(mockFacets).toHaveBeenLastCalledWith("trainer-token", { start: "", end: "" });
  expect(result.current.dateRangeSubtitle).toBe("All dates · Ongoing");

  // A From date picked in the filter panel still narrows it.
  await act(() => result.current.handleFiltersChange({ fromDate: "2026-08-01" }));
  await waitFor(() =>
    expect(mockPage.mock.calls.at(-1)?.[1]).toMatchObject({ status: "ongoing", filters: { start: "2026-08-01", end: "" } }),
  );
  expect(result.current.dateRangeSubtitle).toBe("From 01 Aug · Ongoing");
});

test("the other cards keep the dashboard's date range", async () => {
  mockParams = { tab: "all", status: "planned", start: "2026-10-01", end: "2026-10-05" };
  mockPage.mockImplementation(async (_token, options) => pageOf(options.page ?? 1));
  const { result } = await renderHook(() => useSessionsScreen());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(mockPage.mock.calls.at(-1)?.[1]).toMatchObject({
    status: "planned",
    filters: { start: "2026-10-01", end: "2026-10-05" },
  });
  expect(result.current.dateRangeSubtitle).toBe("01 Oct - 05 Oct · Planned");
});
