// One zone, two spellings: the master list says "North", trainings, trainees and admin grants
// saved before it say "North Zone". Compare zones by this key so both are the same zone - the
// same rule as the backend's app/utils/zones.py (whose access scope sends zones in this form).
const SUFFIX = " zone";

export function zoneKey(value: string | null | undefined): string {
  let key = (value ?? "").trim().toLowerCase();
  if (key.endsWith(SUFFIX)) key = key.slice(0, -SUFFIX.length).trimEnd();
  return key;
}

/** The entry of `names` that is the same zone as `value`, or undefined. */
export function findZone(names: readonly string[], value: string | null | undefined): string | undefined {
  const key = zoneKey(value);
  return key ? names.find((name) => zoneKey(name) === key) : undefined;
}
