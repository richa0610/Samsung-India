import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";
import { ReactNode } from "react";

import { EMPTY_ADMIN_FILTERS } from "@/api/adminFilters";
import { AdminFiltersProvider, useAdminFilters } from "@/hooks/useAdminFilters";

const wrapper = ({ children }: { children: ReactNode }) => <AdminFiltersProvider>{children}</AdminFiltersProvider>;

beforeEach(() => {
  jest.useFakeTimers({ now: new Date("2026-10-15T06:00:00Z") });
});
afterEach(() => {
  jest.useRealTimers();
});

test("the trainer's lists start on the 1st of this month to today; the admin lists stay unfiltered", async () => {
  const { result } = await renderHook(
    () => ({ trainer: useAdminFilters("trainerLists"), admin: useAdminFilters("lists") }),
    { wrapper },
  );
  expect(result.current.trainer.applied).toMatchObject({ start: "2026-10-01", end: "2026-10-15" });
  expect(result.current.admin.applied).toEqual(EMPTY_ADMIN_FILTERS);
});

test("a trainer's own range applies only to the trainer's lists, and Clear goes back to this month so far", async () => {
  const { result } = await renderHook(
    () => ({ trainer: useAdminFilters("trainerLists"), admin: useAdminFilters("lists") }),
    { wrapper },
  );
  await act(() => result.current.trainer.apply({ ...EMPTY_ADMIN_FILTERS, start: "2026-08-01", end: "2026-08-31" }));
  expect(result.current.trainer.applied).toMatchObject({ start: "2026-08-01", end: "2026-08-31" });
  expect(result.current.admin.applied).toEqual(EMPTY_ADMIN_FILTERS);

  await act(() => result.current.trainer.clear());
  expect(result.current.trainer.applied).toMatchObject({ start: "2026-10-01", end: "2026-10-15" });
  expect(result.current.trainer.defaults).toEqual(result.current.trainer.applied);
});
