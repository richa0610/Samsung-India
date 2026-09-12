import AppInput from "@/components/ui/AppInput";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

const FIELDS: { key: "facebookUsername" | "twitterUsername" | "instagramUsername" | "linkedinUsername" | "youtubeUsername" | "github"; label: string; placeholder: string }[] = [
  { key: "facebookUsername", label: "Facebook Username", placeholder: "Facebook URL" },
  { key: "twitterUsername", label: "Twitter Username", placeholder: "Twitter URL" },
  { key: "instagramUsername", label: "Instagram Username", placeholder: "Instagram URL" },
  { key: "linkedinUsername", label: "Linkedin Username", placeholder: "Linkedin URL" },
  { key: "youtubeUsername", label: "YouTube Username", placeholder: "YouTube URL" },
  { key: "github", label: "Github", placeholder: "Github URL" },
];

export function SocialMediaSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.social;

  return (
    <ProfileSection
      icon="share-social-outline"
      title="Social Media Links"
      editing={isEditing}
      saving={savingSection === "social"}
      onToggleEdit={() => (isEditing ? saveSection("social") : toggleEdit("social"))}
    >
      {FIELDS.map((field) => (
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
