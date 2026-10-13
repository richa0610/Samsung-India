import { expect, test } from "@jest/globals";

import { ZONES, regionsForZone } from "@/components/training/add-training/constants";
import { findZone, zoneKey } from "@/utils/zones";

test.each(["North", "North Zone", " north zone ", "NORTH", "North  Zone"])("%j is the north zone", (value) => {
  expect(zoneKey(value)).toBe("north");
});

test("blanks and names without a ' zone' suffix are left alone", () => {
  expect(zoneKey(undefined)).toBe("");
  expect(zoneKey("  ")).toBe("");
  expect(zoneKey("Zone")).toBe("zone");
  expect(zoneKey("Ozone")).toBe("ozone");
});

test("the built-in zones are the master list's names", () => {
  expect([...ZONES].sort()).toEqual(["East", "North", "South", "West"]);
});

test("an older record's 'North Zone' finds the master's 'North' and its regions", () => {
  expect(findZone(ZONES, "North Zone")).toBe("North");
  expect(findZone(ZONES, "")).toBeUndefined();
  expect(findZone(ZONES, "Central")).toBeUndefined();
  expect(regionsForZone("North Zone")).toEqual(regionsForZone("North"));
  expect(regionsForZone("south zone")).toContain("South 1 [KR]");
  expect(regionsForZone(undefined)).toEqual([]);
});
