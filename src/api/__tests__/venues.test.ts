import { beforeEach, expect, jest, test } from "@jest/globals";

import { fetchStateDistricts } from "@/api/locations";
import { fetchVenues } from "@/api/training";

const fetchMock = jest.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({ ok: true, json: async () => [] } as unknown as Response);
  global.fetch = fetchMock;
});

function requestedPath(): string {
  const url = new URL(String(fetchMock.mock.calls[0][0]));
  return url.pathname + url.search;
}

test("the venue list asks for the district in its state, both encoded", async () => {
  await fetchVenues("token", "Aurangabad", "Jammu and Kashmir");
  expect(requestedPath()).toBe("/admin/venues?district=Aurangabad&state=Jammu+and+Kashmir");
});

test("no district, no filter - and a state alone is never sent", async () => {
  await fetchVenues("token", undefined, "Bihar");
  expect(requestedPath()).toBe("/admin/venues");
});

test("the state list is read without signing in", async () => {
  await fetchStateDistricts();
  const [url, options] = fetchMock.mock.calls[0];
  expect(new URL(String(url)).pathname).toBe("/locations/states");
  expect((options?.headers as Record<string, string>).Authorization).toBeUndefined();
});
