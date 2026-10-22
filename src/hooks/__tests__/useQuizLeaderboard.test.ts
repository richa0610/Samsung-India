import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";

import { getCurrentSession, getLiveQuizResults } from "@/api/session";
import { useQuizLeaderboard } from "@/hooks/useQuizLeaderboard";

let mockParams: { conferenceUid?: string } = {};

jest.mock("expo-router", () => ({
  useRouter: () => ({ replace: jest.fn() }),
  useLocalSearchParams: () => mockParams,
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("react-native-safe-area-context", () => ({ useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) }));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ token: "trainee-token", logout: jest.fn() }) }));
jest.mock("@/hooks/useLiveQuizChannel", () => ({ useLiveQuizChannel: () => ({ connected: false }) }));
jest.mock("@/api/session", () => ({
  ...jest.requireActual<object>("@/api/session"),
  getCurrentSession: jest.fn(),
  getLiveQuizResults: jest.fn(),
}));

const mockSession = jest.mocked(getCurrentSession);
const mockResults = jest.mocked(getLiveQuizResults);
const RANKED = { state: "ranked", finished: true, totalQuestions: 3, correctCount: 0, leaderboard: [], you: null } as never;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

beforeEach(() => {
  mockSession.mockReset();
  mockResults.mockReset();
});

test("while the results load the page is loading - never the 'no results' message first", async () => {
  mockParams = { conferenceUid: "CONF-A" };
  mockSession.mockResolvedValue({ conferenceUid: "CONF-A", modules: [] } as never);
  const answer = deferred<never>();
  mockResults.mockReturnValue(answer.promise);
  const { result, unmount } = await renderHook(() => useQuizLeaderboard());
  expect(result.current).toMatchObject({ loading: true, showResults: false });

  await act(async () => answer.resolve(RANKED));
  expect(result.current).toMatchObject({ loading: false, showResults: true });
  await unmount();
});

test("coming back to Rank shows the last results at once while they refresh", async () => {
  mockParams = { conferenceUid: "CONF-B" };
  mockSession.mockResolvedValue({ conferenceUid: "CONF-B", modules: [] } as never);
  mockResults.mockResolvedValue(RANKED);
  const first = await renderHook(() => useQuizLeaderboard());
  expect(first.result.current.showResults).toBe(true);
  await first.unmount();

  mockResults.mockReturnValue(new Promise(() => {}));   // the refresh is still out
  const again = await renderHook(() => useQuizLeaderboard());
  expect(again.result.current).toMatchObject({ loading: false, showResults: true });
  await again.unmount();
});

test("with no Live Quiz results the empty message shows once loading is done", async () => {
  mockParams = { conferenceUid: "CONF-C" };
  mockSession.mockResolvedValue({ conferenceUid: "CONF-C", modules: [] } as never);
  mockResults.mockResolvedValue({ state: "none", finished: false, leaderboard: [], you: null } as never);
  const { result, unmount } = await renderHook(() => useQuizLeaderboard());
  expect(result.current).toMatchObject({ loading: false, showResults: false, liveState: "none" });
  await unmount();
});
