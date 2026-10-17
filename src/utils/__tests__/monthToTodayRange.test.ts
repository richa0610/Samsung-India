import { afterEach, expect, jest, test } from "@jest/globals";
import { monthToTodayRange } from "@/utils/formatDisplayDate";

afterEach(() => {
  jest.useRealTimers();
});

test.each([
  ["2026-10-15T06:00:00Z", "2026-10-01", "2026-10-15"],
  ["2026-10-01T06:00:00Z", "2026-10-01", "2026-10-01"], // the 1st: just today
  ["2026-09-30T18:30:00Z", "2026-10-01", "2026-10-01"], // midnight 1 Oct in India - still September in UTC
  ["2026-09-30T18:29:00Z", "2026-09-01", "2026-09-30"], // 23:59 on 30 Sep in India
  ["2026-12-31T19:00:00Z", "2027-01-01", "2027-01-01"], // new year in India first
])("at %s UTC the month so far in India is %s to %s", (utc, start, end) => {
  jest.useFakeTimers({ now: new Date(utc) });
  expect(monthToTodayRange()).toEqual({ start, end });
});
