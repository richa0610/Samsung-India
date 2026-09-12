export type ProfileSectionKey = "personal" | "address" | "documents" | "social" | "official" | "security";

export const PROFILE_SECTION_FIELDS: Record<ProfileSectionKey, string[]> = {
  personal: ["name", "email", "mobileNumber", "altPhone", "gender", "dob"],
  address: ["city", "district", "state", "pincode", "landmark", "permanentSameAsLocal"],
  // profilePicture is edited via the header avatar's upload flow now
  // (useTrainerProfileForm.handlePickPhoto), not this section - it stays
  // out of this list so saving Documents can't clobber it with a stale
  // value from state.
  documents: ["aadharNumber", "aadharFile", "about", "resume", "otherDocument"],
  social: ["facebookUsername", "twitterUsername", "instagramUsername", "linkedinUsername", "youtubeUsername", "github"],
  official: [
    "jobStatus",
    "joinedOn",
    "role",
    "designation",
    "salary",
    "companyEmail",
    "visitingCard",
    "idCard",
    "offerLetter",
    "letterhead",
    "promocode",
  ],
  security: ["password", "remarks", "agreedToTerms"],
};
