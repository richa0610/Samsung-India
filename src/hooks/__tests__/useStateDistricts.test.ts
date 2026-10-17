import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchStateDistricts } from "@/api/locations";
import { useStateDistricts } from "@/hooks/useStateDistricts";

jest.mock("@/api/locations", () => ({ fetchStateDistricts: jest.fn() }));

const mockFetch = jest.mocked(fetchStateDistricts);

const DIRECTORY = [
  { name: "Bihar", options: ["Aurangabad", "Gaya"] },
  { name: "Maharashtra", options: ["Aurangabad", "Mumbai"] },
  { name: "Uttar Pradesh", options: ["Lucknow"] },
];

beforeEach(() => {
  mockFetch.mockReset();
});

async function render(state: string, district = "") {
  mockFetch.mockResolvedValue(DIRECTORY);
  const { result } = await renderHook(() => useStateDistricts(state, district));
  await waitFor(() => expect(result.current.stateOptions).toHaveLength(3));
  return result;
}

test("every state is offered; no state chosen yet, no districts", async () => {
  const result = await render("");
  expect(result.current.stateOptions.map((option) => option.value)).toEqual(["Bihar", "Maharashtra", "Uttar Pradesh"]);
  expect(result.current.districtOptions).toEqual([]);
});

test("the District options are only the chosen state's own districts", async () => {
  const result = await render("Maharashtra");
  expect(result.current.districtOptions).toEqual([
    { label: "Aurangabad", value: "Aurangabad" },
    { label: "Mumbai", value: "Mumbai" },
  ]);
});

test("a value an older app build saved shows - and would save - as the directory's name", async () => {
  const result = await render("uttar_pradesh", "LUCKNOW");
  expect(result.current.shownState).toBe("Uttar Pradesh");
  expect(result.current.shownDistrict).toBe("Lucknow");
  expect(result.current.districtOptions.map((option) => option.value)).toEqual(["Lucknow"]);
});

test("a value the directory doesn't have is kept as it is", async () => {
  const result = await render("Atlantis", "Nowhere");
  expect(result.current.shownState).toBe("Atlantis");
  expect(result.current.shownDistrict).toBe("Nowhere");
  expect(result.current.districtOptions).toEqual([]);
});

test("a failed load says so, and retry asks again", async () => {
  mockFetch.mockRejectedValueOnce(new Error("offline")).mockResolvedValue(DIRECTORY);
  const { result } = await renderHook(() => useStateDistricts("", ""));
  await waitFor(() => expect(result.current.failed).toBe(true));
  expect(result.current.stateOptions).toEqual([]);

  await act(() => result.current.retry());
  await waitFor(() => expect(result.current.stateOptions).toHaveLength(3));
  expect(result.current.failed).toBe(false);
  expect(mockFetch).toHaveBeenCalledTimes(2);
});
