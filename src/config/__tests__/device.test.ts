import { expect, test } from "@jest/globals";

import { getDeviceId, getDeviceName } from "@/config/device";

test("this install keeps one device ID", () => {
  const first = getDeviceId();
  expect(first).toMatch(/^[a-z0-9]+-[a-z0-9]+-[a-z0-9]+$/);
  expect(getDeviceId()).toBe(first);
});

test("the device has a name to show", () => {
  expect(getDeviceName().length).toBeGreaterThan(0);
});
