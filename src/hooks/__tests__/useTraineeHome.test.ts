import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";
import { Alert } from "react-native";

import { verifyLocation } from "@/api/attendance";
import { getCurrentSession } from "@/api/session";
import { useTraineeHome } from "@/hooks/useTraineeHome";

const mockPush = jest.fn();
const mockRequestLocation = jest.fn<() => Promise<unknown>>();

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  useLocalSearchParams: () => ({}),
  // Treat the screen as focused for as long as the hook is mounted.
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ trainee: { traineeUid: "TRN-1" }, token: "trainee-token", logout: jest.fn() }),
}));
jest.mock("@/api/session", () => ({ ...jest.requireActual<object>("@/api/session"), getCurrentSession: jest.fn() }));
jest.mock("@/api/attendance", () => ({ verifyLocation: jest.fn() }));
jest.mock("@/hooks/useLiveQuizChannel", () => ({ useLiveQuizChannel: () => ({ connected: false }) }));
jest.mock("@/hooks/useLocationPermission", () => ({
  useLocationPermission: () => ({ requestLocationWithRationale: mockRequestLocation }),
}));

const mockGetSession = jest.mocked(getCurrentSession);
const mockVerify = jest.mocked(verifyLocation);

/** A started training, attendance done, with the trainer running the Live Quiz. Each test uses its
 *  own training: the "already taken into the quiz once" marker is per training and outlives a test. */
function liveQuizSession(conferenceUid: string, attendanceGeoFencing: boolean) {
  const module = (key: string, extra: object) => ({
    key,
    name: key,
    time: null,
    endTime: null,
    duration: null,
    isMissed: false,
    completedAt: null,
    score: null,
    assessmentSuiteUid: null,
    ...extra,
  });
  return {
    conferenceUid,
    title: "Training",
    started: true,
    sessionClosed: false,
    attendanceStatus: "Present",
    attendanceGeoFencing,
    modules: [
      module("ATTENDANCE", { isLive: false, isCompleted: true }),
      module("LIVE_QUIZ", { isLive: true, isCompleted: false }),
    ],
  } as never;
}

const enteredLiveQuiz = (conferenceUid: string) =>
  mockPush.mock.calls.some(([route]) => {
    const { pathname, params } = route as { pathname?: string; params?: { conferenceUid?: string } };
    return pathname === "/live_quiz" && params?.conferenceUid === conferenceUid;
  });
const liveQuizCard = (result: { current: ReturnType<typeof useTraineeHome> }) =>
  result.current.activities.find((a) => a.key === "LIVE_QUIZ");

beforeEach(() => {
  mockPush.mockReset();
  mockGetSession.mockReset();
  mockVerify.mockReset();
  mockRequestLocation.mockReset();
  mockRequestLocation.mockResolvedValue({ coords: { latitude: 12.97, longitude: 77.59 }, status: "granted" });
});

test("on a geofenced training the Live Quiz asks for the location check before entering", async () => {
  mockGetSession.mockResolvedValue(liveQuizSession("CONF-GEO", true));
  mockVerify.mockResolvedValue({ withinRadius: true, distanceMeters: 20, radiusMeters: 100, venueLabel: null });
  const { result, unmount } = await renderHook(() => useTraineeHome());

  expect(enteredLiveQuiz("CONF-GEO")).toBe(false);
  expect(liveQuizCard(result)).toMatchObject({ locationGateEnabled: true, locationGateStatus: "idle" });

  await act(async () => result.current.handleCheckInToModule("LIVE_QUIZ"));
  expect(mockVerify).toHaveBeenCalledWith("trainee-token", "CONF-GEO", 12.97, 77.59);
  expect(liveQuizCard(result)?.locationGateStatus).toBe("verified");
  expect(enteredLiveQuiz("CONF-GEO")).toBe(true);
  await unmount();
});

test("outside the venue radius the trainee stays out of the Live Quiz", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  mockGetSession.mockResolvedValue(liveQuizSession("CONF-FAR", true));
  mockVerify.mockResolvedValue({ withinRadius: false, distanceMeters: 900, radiusMeters: 100, venueLabel: null });
  const { result, unmount } = await renderHook(() => useTraineeHome());

  await act(async () => result.current.handleCheckInToModule("LIVE_QUIZ"));
  expect(alert).toHaveBeenCalledWith("You're too far from the venue", expect.any(String));
  expect(liveQuizCard(result)?.locationGateStatus).toBe("idle");
  expect(enteredLiveQuiz("CONF-FAR")).toBe(false);
  alert.mockRestore();
  await unmount();
});

test("a trainee who refuses location permission stays out of the Live Quiz", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  mockGetSession.mockResolvedValue(liveQuizSession("CONF-DENIED", true));
  mockRequestLocation.mockResolvedValue({ coords: null, status: "denied", error: "Location is off" });
  const { result, unmount } = await renderHook(() => useTraineeHome());

  await act(async () => result.current.handleCheckInToModule("LIVE_QUIZ"));
  expect(mockVerify).not.toHaveBeenCalled();
  expect(alert).toHaveBeenCalledWith("Location required", "Location is off");
  expect(enteredLiveQuiz("CONF-DENIED")).toBe(false);
  alert.mockRestore();
  await unmount();
});

test("on a training without geofencing the trainee goes straight into the Live Quiz", async () => {
  mockGetSession.mockResolvedValue(liveQuizSession("CONF-OPEN", false));
  const { result, unmount } = await renderHook(() => useTraineeHome());

  expect(liveQuizCard(result)?.locationGateEnabled).toBe(false);
  expect(enteredLiveQuiz("CONF-OPEN")).toBe(true);
  expect(mockVerify).not.toHaveBeenCalled();
  await unmount();
});
