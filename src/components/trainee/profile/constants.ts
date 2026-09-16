import { Ionicons } from "@expo/vector-icons";

import { STATES } from "@/data/states";

export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;

export type DetailItem = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
};

export function locationLabel(state: string | null, district: string | null) {
  const stateEntry = STATES.find((item) => item.value === state);
  const districtEntry = stateEntry?.cities.find((city) => city.value === district);
  const parts = [districtEntry?.label, stateEntry?.label].filter(Boolean);
  return parts.length ? parts.join(", ") : "--";
}
