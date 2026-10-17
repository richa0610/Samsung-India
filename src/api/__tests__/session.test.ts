import { expect, test } from "@jest/globals";
import { CurrentSession, isSessionLive } from "../session";

test("isSessionLive returns false when session is null or undefined", () => {
  expect(isSessionLive(null)).toBe(false);
  expect(isSessionLive(undefined)).toBe(false);
});

test("isSessionLive returns false when session has not started", () => {
  const session = {
    started: false,
    sessionClosed: false,
  } as CurrentSession;
  expect(isSessionLive(session)).toBe(false);
});

test("isSessionLive returns false when session is closed", () => {
  const session = {
    started: true,
    sessionClosed: true,
  } as CurrentSession;
  expect(isSessionLive(session)).toBe(false);
});

test("isSessionLive returns true when session is started and not closed", () => {
  const session = {
    started: true,
    sessionClosed: false,
  } as CurrentSession;
  expect(isSessionLive(session)).toBe(true);
});
