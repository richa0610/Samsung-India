import { beforeEach, expect, jest, test } from "@jest/globals";

import { fetchStateDistricts } from "@/api/locations";
import { fetchVenues } from "@/api/training";
import { getApiBaseUrl } from "@/constants/api";

const fetchMock = jest.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({ ok: true, json: async () => [] } as unknown as Response);
  global.fetch = fetchMock;
});

// The request's path after the server address - which may itself carry a path
// (e.g. https://tecsoui.com/adm/application/backend).
function requestedPath(): string {
  const url = String(fetchMock.mock.calls[0][0]);
  expect(url.startsWith(getApiBaseUrl())).toBe(true);
  return url.slice(getApiBaseUrl().length);
}

test("the venue list asks for the district in its state, both encoded", async () => {
  await fetchVenues("token", "Aurangabad", "Jammu and Kashmir");
  expect(requestedPath()).toBe("/admin/venues?district=Aurangabad&state=Jammu+and+Kashmir");
});

test("no district, no filter - and a state alone is never sent", async () => {
  await fetchVenues("token", undefined, "Bihar");
  expect(requestedPath()).toBe("/admin/venues");
});

/** A staff token shaped like the server's (header.payload.signature) - only its claims matter here. */
const staffToken = (claims: object) => `h.${Buffer.from(JSON.stringify(claims)).toString("base64url")}.s`;

test("a trainer's staff requests go to the trainer area, an admin's to the admin area", async () => {
  await fetchVenues(staffToken({ sub: "agencyteam:trainer1", role: "trainer" }));
  expect(requestedPath()).toBe("/trainer/venues");
  fetchMock.mockClear();
  await fetchVenues(staffToken({ sub: "admin:super", role: "admin" }));
  expect(requestedPath()).toBe("/admin/venues");
});

test("the state list is read without signing in", async () => {
  await fetchStateDistricts();
  const [, options] = fetchMock.mock.calls[0];
  expect(requestedPath()).toBe("/locations/states");
  expect((options?.headers as Record<string, string>).Authorization).toBeUndefined();
});
