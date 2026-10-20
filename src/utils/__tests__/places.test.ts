import { expect, test } from "@jest/globals";

import { findPlace, placeKey } from "@/utils/places";

test.each(["Uttar Pradesh", "UTTAR PRADESH", " uttar pradesh ", "uttar_pradesh", "up", "UP"])(
  "%j is Uttar Pradesh",
  (value) => {
    expect(placeKey(value)).toBe("uttar pradesh");
  },
);

test("the older list's other odd codes are their places, and blanks are nothing", () => {
  expect(placeKey("dadra_nh_daman_diu")).toBe("dadra and nagar haveli and daman and diu");
  expect(placeKey("chandigarh_city")).toBe("chandigarh");
  expect(placeKey("puducherry_city")).toBe("puducherry");
  expect(placeKey(undefined)).toBe("");
  expect(placeKey("  ")).toBe("");
});

test("findPlace finds a name by any of its spellings, and never matches a blank", () => {
  const names = ["New Delhi", "Uttar Pradesh"];
  expect(findPlace(names, "new_delhi", (name) => name)).toBe("New Delhi");
  expect(findPlace(names, "up", (name) => name)).toBe("Uttar Pradesh");
  expect(findPlace(names, "Atlantis", (name) => name)).toBeUndefined();
  expect(findPlace(names, "", (name) => name)).toBeUndefined();
});
