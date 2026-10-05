import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";
import { ReactNode } from "react";

import { EMPTY_ADMIN_FILTERS } from "@/api/adminFilters";
import { fetchTraineesPage } from "@/api/trainee";
import { AdminFiltersProvider, useAdminFilters } from "@/hooks/useAdminFilters";
import { usePagedTraineeList } from "@/hooks/usePagedTraineeList";

jest.mock("expo-router", () => ({
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "trainer-token" }) }));
jest.mock("@/services/liveEvents", () => ({ subscribe: () => () => {} }));
jest.mock("@/api/trainee", () => ({ fetchTraineesPage: jest.fn() }));

const mockPage = jest.mocked(fetchTraineesPage);
const wrapper = ({ children }: { children: ReactNode }) => <AdminFiltersProvider>{children}</AdminFiltersProvider>;

beforeEach(() => {
  jest.useFakeTimers({ now: new Date("2026-10-15T06:00:00Z"), doNotFake: ["nextTick", "setImmediate"] });
  mockPage.mockReset();
  mockPage.mockResolvedValue({ items: [], total: 0, nextCursor: null } as never);
});
afterEach(() => {
  jest.useRealTimers();
});

test("the trainer's Trainee List asks for trainees registered this month so far", async () => {
  const { result } = await renderHook(() => usePagedTraineeList(false, "trainerLists"), { wrapper });
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(mockPage.mock.calls[0][1]).toMatchObject({ mode: "all", start: "2026-10-01", end: "2026-10-15" });
});

test("a new range reloads from page 1 with those dates", async () => {
  const { result } = await renderHook(
    () => ({ list: usePagedTraineeList(true, "trainerLists"), filters: useAdminFilters("trainerLists") }),
    { wrapper },
  );
  await waitFor(() => expect(result.current.list.loading).toBe(false));

  await act(() => result.current.filters.apply({ ...EMPTY_ADMIN_FILTERS, start: "2026-08-01", end: "2026-09-15" }));
  await waitFor(() => expect(mockPage).toHaveBeenCalledTimes(2));
  expect(mockPage.mock.calls[1][1]).toMatchObject({ mode: "pending", start: "2026-08-01", end: "2026-09-15" });
  expect(mockPage.mock.calls[1][1].page).toBe(1);
});

test("without a range (the admin lists' unfiltered scope) no dates are sent", async () => {
  const { result } = await renderHook(() => usePagedTraineeList(false), { wrapper });
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(mockPage.mock.calls[0][1].start).toBeUndefined();
  expect(mockPage.mock.calls[0][1].end).toBeUndefined();
});
