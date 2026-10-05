import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

const TEXT_FIELDS: { key: "companyEmail" | "visitingCard" | "idCard" | "offerLetter" | "letterhead" | "promocode"; label: string; placeholder?: string }[] = [
  { key: "companyEmail", label: "Company Official Email", placeholder: "official email" },
  { key: "visitingCard", label: "Visiting Card" },
  { key: "idCard", label: "ID Card" },
  { key: "offerLetter", label: "Offer Letter" },
  { key: "letterhead", label: "Letterhead" },
  { key: "promocode", label: "Promocode" },
];

// View-only: these HR details are managed by admins (the server ignores them on a profile save).
export function OfficialInfoSection({ form }: { form: TrainerProfileForm }) {
  const { profile } = form;
  if (!profile) return null;

  return (
    <ProfileSection icon="briefcase-outline" title="Official Information" editing={false}>
      <AppText variant="caption" color={Colors.gray500}>Managed by your admin</AppText>
      <AppInput
        compact
        label="Job Status"
        value={profile.jobStatus}
        editable={false}
      />
      <AppInput
        compact
        label="Joined On"
        value={profile.joinedOn}
        editable={false}
      />
      <AppInput
        compact
        label="Role"
        value={profile.role}
        editable={false}
      />
      <AppInput
        compact
        label="Designation"
        value={profile.designation}
        editable={false}
      />
      <AppInput
        compact
        label="Salary"
        placeholder="Salary in Rupees"
        value={profile.salary}
        editable={false}
      />
      {TEXT_FIELDS.map((field) => (
        <AppInput
          compact
          key={field.key}
          label={field.label}
          placeholder={field.placeholder}
          value={profile[field.key]}
          editable={false}
        />
      ))}
    </ProfileSection>
  );
}
