import { expect, test } from "@jest/globals";

import { isTokenExpired, staffArea } from "@/utils/sessionToken";

/** A token shaped like the server's: header.payload.signature, the payload base64url JSON. */
const token = (payload: object) => `header.${Buffer.from(JSON.stringify(payload)).toString("base64url")}.signature`;

const NOW_MS = 1_800_000_000_000;
const NOW_S = NOW_MS / 1000;

test("a token whose expiry has passed is expired", () => {
  expect(isTokenExpired(token({ exp: NOW_S - 1 }), NOW_MS)).toBe(true);
  expect(isTokenExpired(token({ exp: NOW_S }), NOW_MS)).toBe(true);
});

test("a token before its expiry is not", () => {
  expect(isTokenExpired(token({ exp: NOW_S + 60 }), NOW_MS)).toBe(false);
});

test("base64url payloads decode (the characters plain base64 would write as + and /)", () => {
  const payload = { sub: "admin:a>b?c~~~", exp: NOW_S + 60 };
  expect(Buffer.from(JSON.stringify(payload)).toString("base64url")).toMatch(/[-_]/);
  expect(isTokenExpired(token(payload), NOW_MS)).toBe(false);
  expect(isTokenExpired(token({ ...payload, exp: NOW_S - 60 }), NOW_MS)).toBe(true);
});

test("a token the app can't read is left for the server to judge", () => {
  for (const unreadable of ["", "not-a-token", "a.%%%.c", token({ sub: "no expiry" }), token({ exp: "soon" })]) {
    expect(isTokenExpired(unreadable, NOW_MS)).toBe(false);
  }
});

test("a trainer's token goes to the trainer area, by its role or - without one - its subject", () => {
  expect(staffArea(token({ sub: "agencyteam:trainer1", role: "trainer" }))).toBe("trainer");
  expect(staffArea(token({ sub: "admin:adm_trainer", role: "trainer" }))).toBe("trainer");   // a trainer in the admin table
  expect(staffArea(token({ sub: "agencyteam:trainer1" }))).toBe("trainer");
});

test("an admin's token, and any token the app can't read, goes to the admin area", () => {
  expect(staffArea(token({ sub: "admin:super", role: "admin" }))).toBe("admin");
  expect(staffArea(token({ sub: "agencyteam:x", role: "admin" }))).toBe("admin");   // the role claim decides when present
  for (const unreadable of ["", "not-a-token", "a.%%%.c", token({ exp: NOW_S })]) {
    expect(staffArea(unreadable)).toBe("admin");
  }
});
