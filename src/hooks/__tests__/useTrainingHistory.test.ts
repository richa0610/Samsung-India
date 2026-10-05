import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { getTrainingHistory } from "@/api/session";
import { useTrainingHistory } from "@/hooks/useTrainingHistory";

// The route params the screen was opened with - a Dashboard metric card sets them.
let mockParams: { card?: string; start?: string; end?: string } = {};

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
  useLocalSearchParams: () => mockParams,
  // A focused screen: run the callback like an effect.
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ token: "trainee-token" }) }));
jest.mock("@/api/session", () => ({ getTrainingHistory: jest.fn() }));

const mockHistory = jest.mocked(getTrainingHistory);

const row = (n: number) => ({ conferenceUid: `C${n}`, title: `T${n}`, status: "Completed", rawDate: "2026-09-01" }) as never;
const pageOf = (page: number, totalPages: number, size = 20) => ({
  items: Array.from({ length: size }, (_, i) => row((page - 1) * size + i)),
  total: totalPages * size,
  page,
  pageSize: size,
  totalPages,
});

/** A promise the test resolves itself, to control the order replies arrive in. */
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

beforeEach(() => {
  mockHistory.mockReset();
  mockParams = {};
});

test("loads the first page only, then the next page when asked", async () => {
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 3));
  const { result } = await renderHook(() => useTrainingHistory());

  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(mockHistory).toHaveBeenCalledTimes(1);
  expect(mockHistory.mock.calls[0][1]).toMatchObject({ page: 1, limit: 20 });
  expect(result.current.trainings).toHaveLength(20);
  expect(result.current.hasMore).toBe(true);

  await act(() => result.current.loadMore());
  expect(mockHistory.mock.calls[1][1]).toMatchObject({ page: 2 });
  expect(result.current.trainings).toHaveLength(40);
});

test("two load-more events at once fetch the next page once", async () => {
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 3));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(async () => {
    await Promise.all([result.current.loadMore(), result.current.loadMore()]);
  });
  expect(mockHistory.mock.calls.filter(([, options]) => options.page === 2)).toHaveLength(1);
  expect(result.current.trainings).toHaveLength(40);
});

test("nothing more is fetched after the last page", async () => {
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 5));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(result.current.hasMore).toBe(false);
  await act(() => result.current.loadMore());
  expect(mockHistory).toHaveBeenCalledTimes(1);
});

test("a filter change reloads from page 1 on the server and drops the older reply", async () => {
  const first = deferred<ReturnType<typeof pageOf>>();
  mockHistory.mockImplementationOnce(() => first.promise);
  mockHistory.mockImplementation(async (_token, options) => ({ ...pageOf(options.page, 1, 3) }));
  const { result } = await renderHook(() => useTrainingHistory());

  await act(() => result.current.setStatus("Missed"));
  await waitFor(() => expect(mockHistory).toHaveBeenCalledTimes(2));
  expect(mockHistory.mock.calls[1][1]).toMatchObject({ page: 1, status: "Missed" });
  expect(mockHistory.mock.calls[0][1].signal?.aborted).toBe(true); // the unfiltered request was cancelled

  await waitFor(() => expect(result.current.loading).toBe(false));
  first.resolve(pageOf(1, 5)); // the stale, unfiltered reply arrives late
  await act(async () => {});
  expect(result.current.trainings).toHaveLength(3);
});

test("clearing the filters asks the server for everything again", async () => {
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(() => result.current.setFromDate("2026-09-01"));
  await waitFor(() => expect(mockHistory.mock.calls.at(-1)?.[1]).toMatchObject({ start: "2026-09-01" }));
  await act(() => result.current.clearFilters());
  await waitFor(() => expect(mockHistory.mock.calls.at(-1)?.[1]).toMatchObject({ start: undefined, status: undefined }));
  expect(result.current.hasFilter).toBe(false);
});

test("opened from a Dashboard card, it asks for that card's trainings over the Dashboard's dates", async () => {
  mockParams = { card: "present", start: "2026-09-01", end: "2026-09-30" };
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(mockHistory.mock.calls[0][1]).toMatchObject({ page: 1, card: "present", start: "2026-09-01", end: "2026-09-30" });
  expect(result.current.cardLabel).toBe("Present");
  expect([result.current.fromDate, result.current.toDate]).toEqual(["2026-09-01", "2026-09-30"]);
  expect(result.current.hasFilter).toBe(true);
});

test("removing the card filter keeps the dates; Clear drops everything", async () => {
  mockParams = { card: "absent", start: "2026-09-01" };
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(() => result.current.clearCard());
  await waitFor(() => expect(mockHistory.mock.calls.at(-1)?.[1]).toMatchObject({ card: undefined, start: "2026-09-01" }));
  expect(result.current.cardLabel).toBeNull();

  await act(() => result.current.clearFilters());
  await waitFor(() => expect(mockHistory.mock.calls.at(-1)?.[1]).toMatchObject({ card: undefined, start: undefined }));
  expect(result.current.hasFilter).toBe(false);
});

test("an unknown card in the link is ignored, not sent to the server", async () => {
  for (const card of ["total", "everything", "toString"]) {
    mockHistory.mockReset();
    mockParams = { card };
    mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
    const { result, unmount } = await renderHook(() => useTrainingHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(mockHistory.mock.calls[0][1].card).toBeUndefined();
    expect(result.current.cardLabel).toBeNull();
    await unmount();
  }
});

test("the filter panel starts closed; the filter button opens and closes it", async () => {
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(result.current.filterOpen).toBe(false);
  await act(() => result.current.toggleFilter());
  expect(result.current.filterOpen).toBe(true);
  await act(() => result.current.toggleFilter());
  expect(result.current.filterOpen).toBe(false);
  expect(mockHistory).toHaveBeenCalledTimes(1); // opening/closing the panel doesn't reload the list
});

test("opened from a Dashboard card, the filter panel starts open to show what's applied", async () => {
  mockParams = { card: "ongoing" };
  mockHistory.mockImplementation(async (_token, options) => pageOf(options.page, 1, 2));
  const { result } = await renderHook(() => useTrainingHistory());
  await waitFor(() => expect(result.current.loading).toBe(false));

  expect(result.current.filterOpen).toBe(true);
});
