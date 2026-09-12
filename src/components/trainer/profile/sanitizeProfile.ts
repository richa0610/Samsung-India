/**
 * Per-section validation + sanitization for the trainer profile form.
 * Keeps `useTrainerProfileForm` thin: it just calls these two before PATCHing.
 */

import { TrainerProfile } from "@/api/trainerProfile";
import {
  aadhar12,
  cleanText,
  digitsOnly,
  email,
  firstError,
  mobile10,
  normalizeEmail,
  pincode6,
  ValidationResult,
} from "@/utils/validation";
import { ProfileSectionKey } from "./types";

/** Reject a section save when a format-checked field is filled but malformed. */
export function validateProfileSection(
  section: ProfileSectionKey,
  profile: TrainerProfile,
): ValidationResult {
  switch (section) {
    case "personal":
      return firstError(
        email(profile.email, "Email"),
        mobile10(profile.mobileNumber, "Mobile number"),
        mobile10(profile.altPhone, "Alt phone"),
      );
    case "address":
      return pincode6(profile.pincode);
    case "documents":
      return aadhar12(profile.aadharNumber);
    case "official":
      return email(profile.companyEmail, "Company email");
    default:
      return null;
  }
}

type Cleaner = (value: string) => string;
const text = (max: number): Cleaner => (value) => cleanText(value, max);

// Which editable fields of each section get cleaned, and how. Password is
// deliberately absent - trimming a password can silently change it.
const SECTION_CLEANERS: Partial<
  Record<ProfileSectionKey, Partial<Record<keyof TrainerProfile, Cleaner>>>
> = {
  personal: {
    name: text(120),
    email: normalizeEmail,
    mobileNumber: digitsOnly,
    altPhone: digitsOnly,
    gender: text(20),
    dob: text(20),
  },
  address: {
    city: text(80),
    district: text(80),
    state: text(80),
    pincode: digitsOnly,
    landmark: text(200),
  },
  documents: { aadharNumber: digitsOnly, about: text(1000) },
  social: {
    facebookUsername: text(200),
    twitterUsername: text(200),
    instagramUsername: text(200),
    linkedinUsername: text(200),
    youtubeUsername: text(200),
    github: text(200),
  },
  official: {
    role: text(120),
    designation: text(120),
    salary: digitsOnly,
    companyEmail: normalizeEmail,
    promocode: text(60),
  },
  security: { remarks: text(1000) },
};

/** Return a copy of `profile` with this section's string fields cleaned. */
export function sanitizeProfileSection(
  section: ProfileSectionKey,
  profile: TrainerProfile,
): TrainerProfile {
  const cleaners = SECTION_CLEANERS[section];
  if (!cleaners) return profile;
  const next = { ...profile };
  (Object.keys(cleaners) as (keyof TrainerProfile)[]).forEach((key) => {
    const value = profile[key];
    if (typeof value === "string") {
      (next as Record<string, unknown>)[key] = cleaners[key]!(value);
    }
  });
  return next;
}
