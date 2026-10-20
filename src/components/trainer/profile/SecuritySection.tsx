import { Alert, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { password as validatePassword } from "@/utils/validation/validators";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

export function SecuritySection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.security;

  const handleUpdateChanges = () => {
    if (!profile.password.trim()) {
      Alert.alert("Password required", "Please enter a password before updating.");
      return;
    }
    // Only a NEW password being set here goes through the complexity check -
    // this is a change-password flow, not a login field, so there's no risk
    // of locking someone out of an already-existing password.
    const passwordError = validatePassword(profile.password, "Password");
    if (passwordError) {
      Alert.alert("Password requirements not met", passwordError);
      return;
    }
    if (!profile.agreedToTerms) {
      Alert.alert("Please agree to Terms", "You must agree to the Terms & Conditions to continue.");
      return;
    }
    saveSection("security");
  };

  return (
    <ProfileSection
      icon="lock-closed-outline"
      title="Security"
      editing={isEditing}
      saving={savingSection === "security"}
      onToggleEdit={() => (isEditing ? saveSection("security") : toggleEdit("security"))}
    >
      <AppInput
        compact
        label="Password *"
        placeholder="Password"
        value={profile.password}
        editable={isEditing}
        secureTextEntry
        onChangeText={(v) => setField("password", v)}
      />
      <AppInput compact label="Username" value={profile.username} editable={false} />
      <AppInput
        compact
        label="Remarks"
        value={profile.remarks}
        editable={isEditing}
        multiline
        numberOfLines={3}
        onChangeText={(v) => setField("remarks", v)}
      />

      <View style={styles.warningBanner}>
        <AppText style={styles.warningText} color={Colors.white}>
          Please note: Profile may disable if you update wrong information
        </AppText>
      </View>

      <Pressable style={styles.checkboxRow} onPress={() => setField("agreedToTerms", !profile.agreedToTerms)}>
        <Ionicons
          name={profile.agreedToTerms ? "checkbox" : "square-outline"}
          size={18}
          color={profile.agreedToTerms ? Colors.mainColour1 : Colors.gray400}
        />
        <AppText style={styles.checkboxLabel} color={Colors.gray600}>Agreed to our Terms & Conditions</AppText>
      </Pressable>

      <Pressable style={styles.updateButton} onPress={handleUpdateChanges}>
        <AppText color={Colors.white} weight={FontWeight.semiBold}>Update Changes</AppText>
      </Pressable>
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  warningBanner: { backgroundColor: Colors.pendingColour, borderRadius: Radius.lg, padding: 10, marginBottom: 12 },
  warningText: { fontSize: Fonts.bodySm, textAlign: "center" },
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 16 },
  checkboxLabel: { fontSize: Fonts.bodySm, flex: 1 },
  updateButton: {
    height: 48,
    borderRadius: Radius.xl,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
  },
});
