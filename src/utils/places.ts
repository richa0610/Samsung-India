// One state / district, several spellings: the pincode directory's name ("Uttar Pradesh"), the
// same in capitals, and the codes older app builds saved ("uttar_pradesh", "up"). Compare them
// by this key so all are the same place - the same rule as the backend's app/utils/places.py.

// The old built-in list's codes that aren't simply the name with "_" for each space.
const LEGACY_CODES: Record<string, string> = {
  up: "uttar pradesh",
  "dadra nh daman diu": "dadra and nagar haveli and daman and diu",
  "chandigarh city": "chandigarh",
  "puducherry city": "puducherry",
};

export function placeKey(value: string | null | undefined): string {
  const key = (value ?? "").trim().toLowerCase().replace(/_/g, " ");
  return LEGACY_CODES[key] ?? key;
}

/** The item whose name is `value` in any of its spellings, if there is one. */
export function findPlace<T>(items: T[], value: string | null | undefined, nameOf: (item: T) => string): T | undefined {
  const wanted = placeKey(value);
  return wanted ? items.find((item) => placeKey(nameOf(item)) === wanted) : undefined;
}
