/**
 * Field validators. Each returns an error message when the value is
 * unacceptable, or null when it passes. Framework-agnostic: call them from a
 * hook's submit handler, a react-hook-form `validate` rule, or a test.
 *
 * Format checks accept an empty value on purpose - pair them with `required`
 * where the field is mandatory, so optional fields validate only when filled.
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type ValidationResult = string | null;

/** Non-empty after trimming. */
export function required(
  value: string | null | undefined,
  label = "This field",
): ValidationResult {
  return value && value.trim() ? null : `${label} is required.`;
}

/** Well-formed email address. */
export function email(value: string, label = "Email"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return EMAIL_RE.test(trimmed) ? null : `Enter a valid ${label.toLowerCase()}.`;
}

/** Exactly 10 digits (Indian mobile number). */
export function mobile10(value: string, label = "Phone number"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return /^\d{10}$/.test(trimmed) ? null : `${label} must be a 10 digit mobile number.`;
}

/** Exactly 6 digits (Indian pincode). */
export function pincode6(value: string, label = "Pincode"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return /^\d{6}$/.test(trimmed) ? null : `${label} must be 6 digits.`;
}

/** Exactly 12 digits (Aadhaar number). */
export function aadhar12(value: string, label = "Aadhaar number"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return /^\d{12}$/.test(trimmed) ? null : `${label} must be 12 digits.`;
}

/** Letters, digits and hyphens, 4-15 characters (e.g. "OFF26002", "EMP26001"). */
export function companyId(value: string, label = "Company ID"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return /^[A-Za-z0-9-]{4,15}$/.test(trimmed)
    ? null
    : `${label} must be 4-15 letters, numbers or hyphens.`;
}

/**
 * The standard "every website" password policy: at least 8 characters, with
 * an uppercase letter, a lowercase letter, a digit, and a special character.
 * Reports the first unmet rule rather than one generic message, so the user
 * knows exactly what to fix. Only for a NEW password being set (registration
 * / change-password) - never apply this to a login field, where the account's
 * already-set password could legitimately not match a rule added later.
 */
export function password(value: string, label = "Password"): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (trimmed.length < 8) return `${label} must be at least 8 characters.`;
  if (!/[a-z]/.test(trimmed)) return `${label} must include a lowercase letter.`;
  if (!/[A-Z]/.test(trimmed)) return `${label} must include an uppercase letter.`;
  if (!/\d/.test(trimmed)) return `${label} must include a number.`;
  if (!/[^A-Za-z0-9]/.test(trimmed)) return `${label} must include a special character.`;
  return null;
}

/**
 * Whole number within [min, max]. Empty passes unless `mandatory` is set, so
 * an optional count field only complains once someone types in it.
 */
export function intInRange(
  value: string,
  min: number,
  max: number,
  label = "Value",
  mandatory = false,
): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) return mandatory ? `${label} is required.` : null;
  if (!/^\d+$/.test(trimmed)) return `${label} must be a whole number.`;
  const n = Number(trimmed);
  if (n < min || n > max) return `${label} must be between ${min} and ${max}.`;
  return null;
}

/** First non-null message from a list of results, or null if all pass. */
export function firstError(...results: ValidationResult[]): ValidationResult {
  return results.find((r) => r != null) ?? null;
}
