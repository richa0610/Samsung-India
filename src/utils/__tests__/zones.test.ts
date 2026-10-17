import { expect, test } from "@jest/globals";

import { zoneKey } from "@/utils/zones";

test.each(["North", "North Zone", " north zone ", "NORTH", "North  Zone"])("%j is the north zone", (value) => {
  expect(zoneKey(value)).toBe("north");
});

test("blanks and names without a ' zone' suffix are left alone", () => {
  expect(zoneKey(undefined)).toBe("");
  expect(zoneKey("  ")).toBe("");
  expect(zoneKey("Zone")).toBe("zone");
  expect(zoneKey("Ozone")).toBe("ozone");
});
