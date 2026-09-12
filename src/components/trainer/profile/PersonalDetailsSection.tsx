import AppInput from "@/components/ui/AppInput";
import { digitsOnly } from "@/utils/validation";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

export function PersonalDetailsSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.personal;

  return (
    <ProfileSection
      icon="person-outline"
      title="Personal Details"
      editing={isEditing}
      saving={savingSection === "personal"}
      onToggleEdit={() => (isEditing ? saveSection("personal") : toggleEdit("personal"))}
    >
      <AppInput
        compact
        label="Name *"
        value={profile.name}
        editable={isEditing}
        onChangeText={(v) => setField("name", v)}
      />
      <AppInput
        compact
        label="Email *"
        value={profile.email}
        editable={isEditing}
        keyboardType="email-address"
        autoCapitalize="none"
        onChangeText={(v) => setField("email", v)}
      />
      <AppInput
        compact
        label="Mobile Number *"
        value={profile.mobileNumber}
        editable={isEditing}
        keyboardType="phone-pad"
        maxLength={10}
        onChangeText={(v) => setField("mobileNumber", digitsOnly(v))}
      />
      <AppInput
        compact
        label="Alt Phone"
        value={profile.altPhone}
        editable={isEditing}
        keyboardType="phone-pad"
        maxLength={10}
        onChangeText={(v) => setField("altPhone", digitsOnly(v))}
      />
      <AppInput
        compact
        label="Gender"
        value={profile.gender}
        editable={isEditing}
        onChangeText={(v) => setField("gender", v)}
      />
      <AppInput
        compact
        label="Date Of Birth"
        value={profile.dob}
        editable={isEditing}
        onChangeText={(v) => setField("dob", v)}
      />
    </ProfileSection>
  );
}
