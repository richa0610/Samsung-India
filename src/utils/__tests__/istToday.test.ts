import { afterEach, expect, jest, test } from "@jest/globals";
import { istToday } from "@/utils/formatDisplayDate";

afterEach(() => {
  jest.useRealTimers();
});

test.each([
  ["2026-09-29T18:29:00Z", "2026-09-29"], // 23:59 IST
  ["2026-09-29T18:30:00Z", "2026-09-30"], // midnight IST - still the 29th in UTC
  ["2026-09-30T00:00:00Z", "2026-09-30"], // 05:30 IST
  ["2026-12-31T19:00:00Z", "2027-01-01"], // new year in India first
])("at %s UTC it is %s in India", (utc, expected) => {
  jest.useFakeTimers({ now: new Date(utc) });
  expect(istToday()).toBe(expected);
});
