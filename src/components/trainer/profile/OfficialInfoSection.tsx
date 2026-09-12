import AppInput from "@/components/ui/AppInput";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

const TEXT_FIELDS: { key: "salary" | "companyEmail" | "visitingCard" | "idCard" | "offerLetter" | "letterhead" | "promocode"; label: string; placeholder?: string }[] = [
  { key: "salary", label: "Salary", placeholder: "Salary in Rupees" },
  { key: "companyEmail", label: "Company Official Email", placeholder: "official email" },
  { key: "visitingCard", label: "Visiting Card" },
  { key: "idCard", label: "ID Card" },
  { key: "offerLetter", label: "Offer Letter" },
  { key: "letterhead", label: "Letterhead" },
  { key: "promocode", label: "Promocode" },
];

export function OfficialInfoSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.official;

  return (
    <ProfileSection
      icon="briefcase-outline"
      title="Official Information"
      editing={isEditing}
      saving={savingSection === "official"}
      onToggleEdit={() => (isEditing ? saveSection("official") : toggleEdit("official"))}
    >
      <AppInput
        compact
        label="Job Status"
        value={profile.jobStatus}
        editable={isEditing}
        onChangeText={(v) => setField("jobStatus", v)}
      />
      <AppInput
        compact
        label="Joined On"
        value={profile.joinedOn}
        editable={isEditing}
        onChangeText={(v) => setField("joinedOn", v)}
      />
      <AppInput
        compact
        label="Role"
        value={profile.role}
        editable={isEditing}
        onChangeText={(v) => setField("role", v)}
      />
      <AppInput
        compact
        label="Designation"
        value={profile.designation}
        editable={isEditing}
        onChangeText={(v) => setField("designation", v)}
      />
      {TEXT_FIELDS.map((field) => (
        <AppInput
          compact
          key={field.key}
          label={field.label}
          placeholder={field.placeholder}
          value={profile[field.key]}
          editable={isEditing}
          onChangeText={(v) => setField(field.key, v)}
        />
      ))}
    </ProfileSection>
  );
}
