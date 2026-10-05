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
  intInRange,
  mobile10,
  normalizeEmail,
  pincode6,
  plausibleDob,
  required,
  url,
  ValidationResult,
} from "@/utils/validation";
import { ProfileSectionKey } from "./types";

// Fields genuinely required for a trainer profile, not just decorative "*"
// labels: identity (Name), the number that also doubles as their login
// (Mobile Number), and the region fields real reports/geofencing use
// elsewhere in the app (District, State). City is deliberately excluded -
// nothing outside this one field reads it.
export function validateProfileSection(
  section: ProfileSectionKey,
  profile: TrainerProfile,
): ValidationResult {
  switch (section) {
    case "personal":
      return firstError(
        required(profile.name, "Name"),
        email(profile.email, "Email"),
        required(profile.mobileNumber, "Mobile number"),
        mobile10(profile.mobileNumber, "Mobile number"),
        mobile10(profile.altPhone, "Alt phone"),
        plausibleDob(profile.dob),
      );
    case "address":
      return firstError(
        required(profile.district, "District"),
        required(profile.state, "State"),
        pincode6(profile.pincode),
        // Skipped entirely when permanentSameAsLocal is true - sanitizeProfileSection
        // below overwrites these with the (already-validated) local values before
        // saving, so validating whatever's currently in them here would be
        // validating soon-to-be-discarded data.
        ...(profile.permanentSameAsLocal ? [] : [pincode6(profile.permanentPincode, "Permanent pincode")]),
      );
    case "documents":
      return aadhar12(profile.aadharNumber);
    case "social":
      return firstError(
        url(profile.facebookUsername, "Facebook URL"),
        url(profile.twitterUsername, "Twitter URL"),
        url(profile.instagramUsername, "Instagram URL"),
        url(profile.linkedinUsername, "LinkedIn URL"),
        url(profile.youtubeUsername, "YouTube URL"),
        url(profile.github, "GitHub URL"),
      );
    case "official":
      return firstError(
        email(profile.companyEmail, "Company email"),
        intInRange(profile.salary, 1, 99_999_999, "Salary"),
      );
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
    permanentCity: text(180),
    permanentDistrict: text(180),
    permanentState: text(180),
    permanentPincode: digitsOnly,
    permanentLandmark: text(180),
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
  let next = profile;
  if (cleaners) {
    next = { ...profile };
    (Object.keys(cleaners) as (keyof TrainerProfile)[]).forEach((key) => {
      const value = profile[key];
      if (typeof value === "string") {
        (next as Record<string, unknown>)[key] = cleaners[key]!(value);
      }
    });
  }

  // "Same as local" is enforced here, at save time, rather than by writing
  // into the permanent fields on every local keystroke - the UI only needs
  // to *display* them mirrored while the toggle is on (see
  // LocalAddressSection), and this is the one place that decides what
  // actually reaches the backend.
  if (section === "address" && next.permanentSameAsLocal) {
    next = {
      ...next,
      permanentCity: next.city,
      permanentDistrict: next.district,
      permanentState: next.state,
      permanentPincode: next.pincode,
      permanentLandmark: next.landmark,
    };
  }

  return next;
}
