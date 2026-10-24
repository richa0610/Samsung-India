import { ImageSourcePropType } from "react-native";

import { resolveMediaUrl } from "./media";

type Gender = "male" | "female";

// The same two pictures the server gives a trainer without a photo (backend/media/trainer_photos).
const AVATAR_BY_GENDER: Record<Gender, ImageSourcePropType> = {
  male: require("@/assets/images/user_img/default_male.png"),
  female: require("@/assets/images/user_img/default_female.png"),
};

/** "male" / "female" however the gender was typed - any letter case, spaces around it, or just its
 *  first letter ("M", "f") - or null for anything else (blank, "Other", ...). */
export function genderKey(gender: string | null | undefined): Gender | null {
  const value = (gender ?? "").trim().toLowerCase();
  if (value === "male" || value === "m") return "male";
  if (value === "female" || value === "f") return "female";
  return null;
}

// `profilePhoto` often carries a placeholder filename ("default.png", etc.)
// rather than a real upload - those are NOT an image URL, they mean "no
// photo, fall back to the gender icon".
const PLACEHOLDER_PHOTOS = new Set(["default.png", "default", "user_icon.png", "avatar.png"]);

function isRealPhoto(value: string | null | undefined): boolean {
  if (!value) return false;
  return !PLACEHOLDER_PHOTOS.has(value.trim().toLowerCase());
}

/**
 * The trainee's avatar picture - one source of truth for every trainee
 * screen, which all show it through `components/common/TraineeAvatar`:
 *   1. their uploaded profile photo, if there's a real one
 *   2. a male / female picture by `gender` (see genderKey)
 *   3. null when gender is unknown - TraineeAvatar then shows their initials,
 *      never a picture of someone who may look nothing like them
 *
 * `/media` now requires a bearer token (was an open static mount), so a
 * real photo needs `token` - the trainee's own session token - attached as
 * a request header; callers get it from `useAuth()`.
 */
export function traineeAvatar(
  input: { gender?: string | null; profilePhoto?: string | null } | null | undefined,
  token?: string | null,
): ImageSourcePropType | null {
  if (isRealPhoto(input?.profilePhoto)) {
    const photoUrl = resolveMediaUrl(input?.profilePhoto);
    if (photoUrl) {
      return token ? { uri: photoUrl, headers: { Authorization: `Bearer ${token}` } } : { uri: photoUrl };
    }
  }
  const gender = genderKey(input?.gender);
  return gender ? AVATAR_BY_GENDER[gender] : null;
}
