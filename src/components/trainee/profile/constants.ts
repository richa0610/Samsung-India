import { Ionicons } from "@expo/vector-icons";

export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;

export type DetailItem = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
};

/** A profile value as shown: the saved value, or "--" when there is none - never a made-up one. */
export function shownValue(value: string | number | null | undefined): string {
  const text = value === null || value === undefined ? "" : String(value).trim();
  return text || "--";
}

/** A saved state / district as words. Older records hold the old built-in list's codes
 *  ("new_delhi", "up"); those read "New Delhi", "UP". A saved name is kept as it is. */
export function placeName(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!/^[a-z_]+$/.test(text)) return text;
  if (text.length <= 3) return text.toUpperCase();
  return text
    .split("_")
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}
