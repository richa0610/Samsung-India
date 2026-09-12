/**
 * Pure string sanitizers shared by every form in the app.
 * No React, no side effects - safe to call from a hook, a react-hook-form
 * rule, or a unit test.
 */

// \p{Cc} = C0/C1 control chars, \p{Cf} = format chars (zero-width joiners,
// bidi overrides, BOM). None of these belong in a form field - they break
// layout, search and backend parsing when pasted in.
const CONTROL_CHARS = /[\p{Cc}\p{Cf}]/gu;

/** Drop non-printable / zero-width / control characters. */
export function stripControlChars(value: string): string {
  return value.replace(CONTROL_CHARS, "");
}

/** Trim the ends and collapse every inner whitespace run to a single space. */
export function trimCollapse(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

/** Keep digits only - for phone, pincode, aadhaar and numeric-count fields. */
export function digitsOnly(value: string): string {
  return value.replace(/[^0-9]/g, "");
}

/** Trim + lowercase - the canonical stored form of an email address. */
export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

/** Hard cap a string's length (defensive - most inputs also set maxLength). */
export function capLength(value: string, max: number): string {
  return value.length > max ? value.slice(0, max) : value;
}

/**
 * Default cleaner for free-text fields: strip control chars, collapse
 * whitespace, cap length. Run this on any user text before sending it to the
 * API. Returns "" for an all-whitespace input so callers can `|| undefined`.
 */
export function cleanText(value: string, max = 500): string {
  return capLength(trimCollapse(stripControlChars(value)), max);
}
