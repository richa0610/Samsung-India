import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchTrainerSummary } from "@/api/training";
import { useTrainerDashboardScreen } from "../useTrainerDashboardScreen";

const mockPush = jest.fn();

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ admin: null, adminToken: "trainer-token" }) }));
jest.mock("@/hooks/useStaffLogout", () => ({
  useStaffLogout: () => ({ confirmLogoutOpen: false, requestLogout: jest.fn(), cancelLogout: jest.fn(), confirmLogout: jest.fn() }),
}));
jest.mock("@/services/liveEvents", () => ({ subscribe: () => () => {} }));
jest.mock("@/api/training", () => ({ fetchTrainerSummary: jest.fn() }));

const mockSummary = jest.mocked(fetchTrainerSummary);

beforeEach(() => {
  mockPush.mockReset();
  mockSummary.mockReset();
  mockSummary.mockResolvedValue({
    totalSessions: 0,
    completed: 0,
    pending: 0,
    missed: 0,
    ongoing: 1,
    executedPercentage: 0,
    pendingPercentage: 0,
    recentCompleted: [],
  } as never);
});

async function renderDashboard() {
  const { result } = await renderHook(() => useTrainerDashboardScreen());
  await waitFor(() => expect(result.current.stats.ongoing).toBe(1));
  return result;
}

test("the Ongoing card opens every running training, without the date filter", async () => {
  const result = await renderDashboard();

  await act(() => result.current.handleStatCardPress("ongoing"));

  expect(mockPush).toHaveBeenLastCalledWith({ pathname: "/sessions", params: { tab: "all", status: "ongoing" } });
});

test("the other cards open their list for the dashboard's date range", async () => {
  const result = await renderDashboard();

  await act(() => result.current.handleStatCardPress("planned"));

  expect(mockPush).toHaveBeenLastCalledWith({
    pathname: "/sessions",
    params: { tab: "all", status: "planned", start: expect.any(String), end: expect.any(String) },
  });
});
