import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchTrainingsPage } from "@/api/training";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

jest.mock("expo-router", () => ({
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "admin-token" }) }));
jest.mock("@/hooks/useAdminFilters", () => {
  const applied = {};
  return { useAdminFilters: () => ({ applied, appliedKey: "{}" }) };
});
jest.mock("@/services/liveEvents", () => ({ subscribe: () => () => {} }));
jest.mock("@/api/training", () => ({ fetchTrainingsPage: jest.fn() }));

const mockPage = jest.mocked(fetchTrainingsPage);
const pageOf = (page: number) =>
  ({ items: [{ conferenceUid: `C${page}` }], total: 30, page, pageSize: 10, totalPages: 3, nextCursor: null }) as never;

beforeEach(() => {
  mockPage.mockReset();
});

test("opening the list fetches only the page shown - no speculative next page", async () => {
  mockPage.mockImplementation(async (_token, options) => pageOf(options.page ?? 1));
  const { result } = await renderHook(() => usePagedTrainingList(false));
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(mockPage).toHaveBeenCalledTimes(1);

  await act(() => result.current.setPage(2));
  await waitFor(() => expect(mockPage).toHaveBeenCalledTimes(2));
  expect(mockPage.mock.calls[1][1]).toMatchObject({ page: 2 });

  await act(() => result.current.setPage(1)); // back to a page already seen: from memory
  expect(mockPage).toHaveBeenCalledTimes(2);
  expect(result.current.items).toEqual([{ conferenceUid: "C1" }]);
});

test("a newer request cancels the one still on its way", async () => {
  const pending: ((value: never) => void)[] = [];
  mockPage.mockImplementation(() => new Promise((resolve) => pending.push(resolve)));
  const { result } = await renderHook(() => usePagedTrainingList(false));

  await act(() => result.current.setSearch("delhi"));
  await waitFor(() => expect(mockPage).toHaveBeenCalledTimes(2));
  expect(mockPage.mock.calls[0][1].signal?.aborted).toBe(true);
  expect(mockPage.mock.calls[1][1]).toMatchObject({ q: "delhi" });
  expect(mockPage.mock.calls[1][1].signal?.aborted).toBe(false);

  await act(async () => {
    pending[1](pageOf(1));
    pending[0]({ items: [{ conferenceUid: "STALE" }], total: 99, totalPages: 10, page: 1, pageSize: 10 } as never);
  });
  expect(result.current.items).toEqual([{ conferenceUid: "C1" }]);
});
