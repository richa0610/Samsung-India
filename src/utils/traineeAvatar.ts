import { ImageSourcePropType } from "react-native";

import { resolveMediaUrl } from "./media";

const AVATAR_BY_GENDER: Record<string, ImageSourcePropType> = {
  male: require("@/assets/images/user_img/default_male.png"),
  female: require("@/assets/images/user_img/default_female.png"),
};
const NEUTRAL_AVATAR: ImageSourcePropType = require("@/assets/images/Icons/face_icon.png");

// `profilePhoto` often carries a placeholder filename ("default.png", etc.)
// rather than a real upload - those are NOT an image URL, they mean "no
// photo, fall back to the gender icon".
const PLACEHOLDER_PHOTOS = new Set(["default.png", "default", "user_icon.png", "avatar.png"]);

function isRealPhoto(value: string | null | undefined): boolean {
  if (!value) return false;
  return !PLACEHOLDER_PHOTOS.has(value.trim().toLowerCase());
}

/**
 * The trainee's avatar - one source of truth so the Join Session screen
 * (`components/session/join`) and the session-detail header
 * (`TrainingSessionHeader`) always show the same thing:
 *   1. their uploaded profile photo, if there's a real one
 *   2. a male / female icon by `gender`
 *   3. a neutral face icon when gender is unknown
 *
 * `/media` now requires a bearer token (was an open static mount), so a
 * real photo needs `token` - the trainee's own session token - attached as
 * a request header; callers get it from `useAuth()`.
 */
export function traineeAvatar(
  input: { gender?: string | null; profilePhoto?: string | null } | null | undefined,
  token?: string | null,
): ImageSourcePropType {
  if (isRealPhoto(input?.profilePhoto)) {
    const photoUrl = resolveMediaUrl(input?.profilePhoto);
    if (photoUrl) {
      return token ? { uri: photoUrl, headers: { Authorization: `Bearer ${token}` } } : { uri: photoUrl };
    }
  }
  return AVATAR_BY_GENDER[input?.gender?.toLowerCase() ?? ""] ?? NEUTRAL_AVATAR;
}
