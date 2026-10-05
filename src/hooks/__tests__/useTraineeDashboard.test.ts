import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";

import { useTraineeDashboard } from "@/hooks/useTraineeDashboard";

const mockPush = jest.fn();
// The Dashboard's own date filter (AdminFilterBar scope "trainee"), "" when unset.
const mockApplied = { start: "", end: "" };

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  // Treat the screen as focused for as long as the hook is mounted.
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ trainee: null, token: "trainee-token", logout: jest.fn() }) }));
jest.mock("@/hooks/useAdminFilters", () => ({
  useAdminFilters: () => ({ applied: mockApplied, appliedKey: JSON.stringify(mockApplied) }),
}));
jest.mock("@/api/session", () => ({
  getCurrentSession: jest.fn(() => Promise.reject(new Error("no session"))),
  getTraineeDashboard: jest.fn(() => Promise.resolve(null)),
}));

beforeEach(() => {
  mockPush.mockReset();
  mockApplied.start = "";
  mockApplied.end = "";
});

test("a metric card opens Training History with that card over the Dashboard's dates", async () => {
  mockApplied.start = "2026-09-01";
  mockApplied.end = "2026-09-30";
  const { result, unmount } = await renderHook(() => useTraineeDashboard());

  await act(() => result.current.handleMetricCardPress("present"));
  expect(mockPush).toHaveBeenLastCalledWith({
    pathname: "/training_history",
    params: { card: "present", start: "2026-09-01", end: "2026-09-30" },
  });
  await unmount();
});

test("Total Trainings opens every training in range; no date filter sends no dates", async () => {
  const { result, unmount } = await renderHook(() => useTraineeDashboard());

  await act(() => result.current.handleMetricCardPress("total"));
  expect(mockPush).toHaveBeenLastCalledWith({ pathname: "/training_history", params: {} });

  await act(() => result.current.handleMetricCardPress("notStarted"));
  expect(mockPush).toHaveBeenLastCalledWith({ pathname: "/training_history", params: { card: "notStarted" } });
  await unmount();
});
