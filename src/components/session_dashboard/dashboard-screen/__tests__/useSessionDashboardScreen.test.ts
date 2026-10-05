import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";

import { Alert } from "react-native";

import { ApiError } from "@/api/client";
import { fetchSessionDashboard, stopLiveTimer } from "@/api/training";
import { useSessionDashboardScreen } from "../useSessionDashboardScreen";

const mockReplace = jest.fn();
const mockAuth = { admin: { role: "trainer" }, adminToken: "trainer-token" };
const mockParams = { conferenceUid: "CONF-1", from: undefined as string | undefined };

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: mockReplace }),
  useLocalSearchParams: () => mockParams,
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => mockAuth }));
jest.mock("@/api/training", () => ({
  fetchSessionDashboard: jest.fn(),
  broadcastLiveQuestion: jest.fn(),
  checkTrainingSchedule: jest.fn(),
  endTraining: jest.fn(),
  markAttendance: jest.fn(),
  restartModule: jest.fn(),
  showLiveLeaderboard: jest.fn(),
  showLiveLobby: jest.fn(),
  startModule: jest.fn(),
  startTraining: jest.fn(),
  stopActiveModule: jest.fn(),
  stopLiveTimer: jest.fn(),
}));
// Captures the Live Quiz nudge callback, so a test can fire nudges like the live room does.
const mockNudge = { current: () => {} };
jest.mock("@/hooks/useLiveQuizChannel", () => ({
  useLiveQuizChannel: (_uid: string, _token: string, onNudge: () => void) => {
    mockNudge.current = onNudge;
  },
}));
jest.mock("@/hooks/useLocationPermission", () => ({ useLocationPermission: () => ({ requestLocationWithRationale: jest.fn() }) }));
jest.mock("@/services/locationService", () => ({
  checkLocationPermission: jest.fn(() => Promise.resolve("denied")),
  getCurrentCoordinates: jest.fn(() => Promise.resolve(null)),
}));

const mockFetch = jest.mocked(fetchSessionDashboard);
const mockStopTimer = jest.mocked(stopLiveTimer);
const dashboard = (conferenceStatus: string, marker = 0) => ({ conferenceUid: "CONF-1", conferenceStatus, marker }) as never;
/** A Live Quiz question on screen - running (`timerRemainingMs` null) or stopped with that much left. */
const liveDashboard = (timerRemainingMs: number | null) =>
  ({
    conferenceUid: "CONF-1",
    conferenceStatus: "Ongoing",
    liveStudio: { state: "QUESTION_LIVE", timerRemainingMs },
  }) as never;
const shownTimerRemainingMs = (result: { current: ReturnType<typeof useSessionDashboardScreen> }) =>
  result.current.data?.liveStudio?.timerRemainingMs;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

beforeEach(() => {
  mockFetch.mockReset();
  mockStopTimer.mockReset();
  mockReplace.mockReset();
  mockAuth.admin = { role: "trainer" };
  mockParams.from = undefined;
  jest.useFakeTimers();
});
afterEach(() => {
  jest.useRealTimers();
});

test("a burst of live nudges during a load costs one follow-up request, not one each", async () => {
  const first = deferred<never>();
  mockFetch.mockImplementationOnce(() => first.promise);
  mockFetch.mockImplementation(async () => dashboard("Ongoing"));
  const { unmount } = await renderHook(() => useSessionDashboardScreen());
  expect(mockFetch).toHaveBeenCalledTimes(1);

  await act(async () => {
    for (let i = 0; i < 25; i++) mockNudge.current(); // 25 trainees answer while the first load is out
  });
  expect(mockFetch).toHaveBeenCalledTimes(1);

  await act(async () => first.resolve(dashboard("Ongoing")));
  expect(mockFetch).toHaveBeenCalledTimes(2); // exactly one follow-up
  await unmount();
});

test("a running session is polled every 5 s, a finished one is not", async () => {
  mockFetch.mockImplementation(async () => dashboard("Ongoing"));
  const live = await renderHook(() => useSessionDashboardScreen());
  for (let tick = 0; tick < 3; tick++) {
    await act(async () => jest.advanceTimersByTime(5_000)); // each poll's reply arrives before the next tick
  }
  expect(mockFetch).toHaveBeenCalledTimes(4); // the first load + 3 polls
  await live.unmount();

  mockFetch.mockReset();
  mockFetch.mockImplementation(async () => dashboard("Completed"));
  const done = await renderHook(() => useSessionDashboardScreen());
  for (let tick = 0; tick < 3; tick++) {
    await act(async () => jest.advanceTimersByTime(5_000));
  }
  expect(mockFetch).toHaveBeenCalledTimes(1);
  await done.unmount();
});

test("an older reply never overwrites a newer one", async () => {
  jest.useRealTimers(); // no polling involved; the 5 s poll can't fire within this test
  const slowSilent = deferred<never>();
  mockFetch.mockImplementationOnce(async () => dashboard("Ongoing", 1)); // first load
  mockFetch.mockImplementationOnce(() => slowSilent.promise); // a background refresh that is slow
  mockFetch.mockImplementationOnce(async () => dashboard("Ongoing", 3)); // the user's pull-to-refresh
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());

  await act(async () => {
    mockNudge.current(); // starts the slow background refresh (not awaited - it stays pending)
  });
  await act(async () => result.current.loadData("refresh"));
  expect((result.current.data as unknown as { marker: number }).marker).toBe(3);

  await act(async () => slowSilent.resolve(dashboard("Ongoing", 2))); // the older reply arrives last
  expect((result.current.data as unknown as { marker: number }).marker).toBe(3);
  await unmount();
});

test("when admin ends session, redirects to /admin_training_list", async () => {
  mockAuth.admin = { role: "admin" };
  mockFetch.mockImplementation(async () => dashboard("Ongoing"));
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());

  const photo = { uri: "file://photo.jpg", name: "photo.jpg", type: "image/jpeg" };
  const sheet = { uri: "file://sheet.pdf", name: "sheet.pdf", type: "application/pdf" };
  await act(async () => {
    await result.current.handleConfirmEndSession(photo, sheet, 25);
  });

  expect(mockReplace).toHaveBeenCalledWith("/admin_training_list");
  await unmount();
});

test("when trainer ends session, redirects to /trainer_dashboard", async () => {
  mockAuth.admin = { role: "trainer" };
  mockFetch.mockImplementation(async () => dashboard("Ongoing"));
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());

  const photo = { uri: "file://photo.jpg", name: "photo.jpg", type: "image/jpeg" };
  const sheet = { uri: "file://sheet.pdf", name: "sheet.pdf", type: "application/pdf" };
  await act(async () => {
    await result.current.handleConfirmEndSession(photo, sheet, 25);
  });

  expect(mockReplace).toHaveBeenCalledWith("/trainer_dashboard");
  await unmount();
});

test("Stop Timer sends the button the trainer sees: Stop while running, Play while stopped", async () => {
  mockFetch.mockImplementation(async () => liveDashboard(null));
  mockStopTimer.mockResolvedValueOnce(liveDashboard(20_000)).mockResolvedValueOnce(liveDashboard(null));
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());

  await act(async () => result.current.liveQuizControls.onStopTimer());
  expect(mockStopTimer).toHaveBeenLastCalledWith("trainer-token", "CONF-1", true);
  expect(shownTimerRemainingMs(result)).toBe(20_000);

  await act(async () => result.current.liveQuizControls.onStopTimer());
  expect(mockStopTimer).toHaveBeenLastCalledWith("trainer-token", "CONF-1", false);
  expect(shownTimerRemainingMs(result)).toBeNull();
  await unmount();
});

test("a refresh sent before Stop Timer was pressed can't flip it back on screen", async () => {
  jest.useRealTimers(); // no polling involved; the 5 s poll can't fire within this test
  const slowSilent = deferred<never>();
  mockFetch.mockImplementationOnce(async () => liveDashboard(null)); // first load: running
  mockFetch.mockImplementationOnce(() => slowSilent.promise); // a background refresh that is slow
  mockFetch.mockImplementation(async () => liveDashboard(20_000)); // any refresh after the press
  mockStopTimer.mockResolvedValueOnce(liveDashboard(20_000));
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());

  await act(async () => {
    mockNudge.current(); // starts the slow background refresh (not awaited - it stays pending)
  });
  await act(async () => result.current.liveQuizControls.onStopTimer());
  expect(shownTimerRemainingMs(result)).toBe(20_000);

  await act(async () => slowSilent.resolve(liveDashboard(null))); // its pre-Stop reply arrives last
  expect(shownTimerRemainingMs(result)).toBe(20_000);

  const requestsSoFar = mockFetch.mock.calls.length;
  await act(async () => {
    mockNudge.current(); // background refreshes still run afterwards
  });
  expect(mockFetch).toHaveBeenCalledTimes(requestsSoFar + 1);
  await unmount();
});

test("a Stop Timer the server refuses is reported and the dashboard reloaded", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  mockFetch.mockImplementation(async () => liveDashboard(null));
  mockStopTimer.mockRejectedValueOnce(new ApiError("No question is currently live", 409));
  const { result, unmount } = await renderHook(() => useSessionDashboardScreen());
  const requestsSoFar = mockFetch.mock.calls.length;

  await act(async () => result.current.liveQuizControls.onStopTimer());
  expect(alert).toHaveBeenCalledWith("Couldn't stop the timer", "No question is currently live");
  expect(mockFetch).toHaveBeenCalledTimes(requestsSoFar + 1);
  expect(result.current.liveQuizControls.stoppingTimer).toBe(false);
  alert.mockRestore();
  await unmount();
});
