export type ProfileSectionKey = "personal" | "address" | "documents" | "social" | "official" | "security";

export const PROFILE_SECTION_FIELDS: Record<ProfileSectionKey, string[]> = {
  personal: ["name", "email", "mobileNumber", "altPhone", "gender", "dob"],
  address: [
    "city", "district", "state", "pincode", "landmark",
    "permanentSameAsLocal",
    "permanentCity", "permanentDistrict", "permanentState", "permanentPincode", "permanentLandmark",
  ],
  // profilePicture and aadharFile are each edited via their own immediate
  // upload flow now (useTrainerProfileForm.handlePickPhoto/handlePickAadhar),
  // not this section - they stay out of this list so saving Documents can't
  // clobber them with a stale value from state.
  documents: ["aadharNumber", "about", "resume", "otherDocument"],
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
