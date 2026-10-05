import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchTrainingFacets, fetchTrainingsPage } from "@/api/training";
import { useSessionsScreen } from "../useSessionsScreen";

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
  useLocalSearchParams: () => ({}),
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "trainer-token" }) }));
jest.mock("@/api/training", () => ({ fetchTrainingsPage: jest.fn(), fetchTrainingFacets: jest.fn() }));

const mockPage = jest.mocked(fetchTrainingsPage);
const mockFacets = jest.mocked(fetchTrainingFacets);
const pageOf = (page: number) =>
  ({ items: [{ conferenceUid: `C${page}` }], total: 60, page, pageSize: 20, totalPages: 3, nextCursor: null }) as never;

beforeEach(() => {
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
