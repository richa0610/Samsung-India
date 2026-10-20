import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchZoneRegions } from "@/api/locations";
import { useZoneRegions } from "@/hooks/useZoneRegions";

jest.mock("@/api/locations", () => ({ fetchZoneRegions: jest.fn() }));

const mockFetch = jest.mocked(fetchZoneRegions);

const MASTER = [
  { name: "North", options: ["North 1", "North 2"] },
  { name: "South", options: ["South 1"] },
];

beforeEach(() => {
  mockFetch.mockReset();
});

async function render(zone: string) {
  mockFetch.mockResolvedValue(MASTER);
  const { result } = await renderHook(() => useZoneRegions(zone));
  await waitFor(() => expect(result.current.zoneOptions).toHaveLength(2));
  return result;
}

test("every zone is offered; no zone chosen yet, no regions", async () => {
  const result = await render("");
  expect(result.current.zoneOptions.map((option) => option.value)).toEqual(["North", "South"]);
  expect(result.current.regionOptions).toEqual([]);
});

test("the Region options are only the chosen zone's own, whichever way the zone is spelled", async () => {
  for (const zone of ["North", "North Zone"]) {
    const result = await render(zone);
    expect(result.current.regionOptions.map((option) => option.value)).toEqual(["North 1", "North 2"]);
  }
});

test("a list that couldn't load says so, and can be asked for again", async () => {
  mockFetch.mockRejectedValueOnce(new Error("offline"));
  const { result } = await renderHook(() => useZoneRegions(""));
  await waitFor(() => expect(result.current.failed).toBe(true));

  mockFetch.mockResolvedValue(MASTER);
  await act(async () => {
    result.current.retry();
  });
  await waitFor(() => expect(result.current.zoneOptions).toHaveLength(2));
  expect(result.current.failed).toBe(false);
});
