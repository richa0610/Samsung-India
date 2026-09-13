import { ActivityIndicator, Alert, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { digitsOnly } from "@/utils/validation";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

function FileFieldLabel({ label }: { label: string }) {
  return (
    <View style={styles.labelRow}>
      <AppText style={styles.label} color={Colors.black}>{label}</AppText>
      <Pressable onPress={() => Alert.alert("No file uploaded yet", "This trainee hasn't uploaded a file for this field.")}>
        <AppText style={styles.viewExisting} color={Colors.mainColour1}>(View Existing)</AppText>
      </Pressable>
    </View>
  );
}

// Aadhaar is a real upload (JPEG/PNG/PDF/Word), not free text like Resume/
// Other Document still are - shows an upload button when nothing's on file
// yet, or the current filename with a Replace action once something is.
function AadharFileField({
  value,
  editable,
  uploading,
  onPick,
}: {
  value: string;
  editable: boolean;
  uploading: boolean;
  onPick: () => void;
}) {
  const filename = value ? value.split("/").pop() : null;

  return (
    <View style={styles.fieldBlock}>
      <AppText style={styles.label} color={Colors.black}>Aadhar (File)</AppText>
      {filename ? (
        <View style={styles.fileRow}>
          <Ionicons name="document-text-outline" size={16} color="#374151" />
          <AppText style={styles.fileName} numberOfLines={1}>{filename}</AppText>
          {editable && (
            <Pressable onPress={onPick} disabled={uploading} hitSlop={8}>
              <AppText style={styles.replaceText} color={Colors.mainColour1} weight={FontWeight.semiBold}>
                {uploading ? "Uploading…" : "Replace"}
              </AppText>
            </Pressable>
          )}
        </View>
      ) : (
        editable && (
          <Pressable style={styles.uploadBtn} onPress={onPick} disabled={uploading} accessibilityRole="button">
            {uploading ? (
              <ActivityIndicator size="small" color="#0066FF" />
            ) : (
              <Ionicons name="cloud-upload-outline" size={18} color="#0066FF" />
            )}
            <AppText color="#0066FF" weight={FontWeight.semiBold} style={styles.uploadText}>
              {uploading ? "Uploading…" : "Upload Aadhar (JPEG, PNG, PDF or Word)"}
            </AppText>
          </Pressable>
        )
      )}
      {!filename && !editable && (
        <AppText style={styles.notUploadedText} color={Colors.gray400}>Not uploaded yet</AppText>
      )}
    </View>
  );
}

export function DocumentsSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, uploadingAadhar, setField, toggleEdit, saveSection, handlePickAadhar } = form;
  if (!profile) return null;
  const isEditing = editing.documents;

  return (
    <ProfileSection
      icon="document-text-outline"
      title="Documents"
      editing={isEditing}
      saving={savingSection === "documents"}
      onToggleEdit={() => (isEditing ? saveSection("documents") : toggleEdit("documents"))}
    >
      <AppInput
        compact
        label="Aadhar Number"
        placeholder="Enter 12 Digit Aadhar Number"
        value={profile.aadharNumber}
        editable={isEditing}
        keyboardType="number-pad"
        maxLength={12}
        onChangeText={(v) => setField("aadharNumber", digitsOnly(v))}
      />
      <AadharFileField
        value={profile.aadharFile}
        editable={isEditing}
        uploading={uploadingAadhar}
        onPick={handlePickAadhar}
      />
      <AppInput
        compact
        label="About"
        value={profile.about}
        editable={isEditing}
        multiline
        numberOfLines={3}
        onChangeText={(v) => setField("about", v)}
      />
      <FileFieldLabel label="Resume" />
      <AppInput compact value={profile.resume} editable={isEditing} onChangeText={(v) => setField("resume", v)} />
      <FileFieldLabel label="Other Document" />
      <AppInput
        compact
        value={profile.otherDocument}
        editable={isEditing}
        onChangeText={(v) => setField("otherDocument", v)}
      />
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  labelRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 8 },
  label: { fontSize: Fonts.body, marginBottom: 8 },
  viewExisting: { fontSize: Fonts.bodySm },
  fieldBlock: { marginBottom: 12 },
  uploadBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: 44,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: "#BFDBFE",
    backgroundColor: "#EFF6FF",
  },
  uploadText: { fontSize: 13, flexShrink: 1, textAlign: "center" },
  fileRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    height: 44,
    paddingHorizontal: 12,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: Colors.white,
  },
  fileName: { flex: 1, fontSize: 12, color: "#374151" },
  replaceText: { fontSize: 13 },
  notUploadedText: { fontSize: Fonts.bodySm },
});
