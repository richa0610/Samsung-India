import { Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { digitsOnly } from "@/utils/validation";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

export function LocalAddressSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.address;

  return (
    <ProfileSection
      icon="location-outline"
      title="Local Address"
      editing={isEditing}
      saving={savingSection === "address"}
      onToggleEdit={() => (isEditing ? saveSection("address") : toggleEdit("address"))}
    >
      <AppInput
        compact
        label="City *"
        value={profile.city}
        editable={isEditing}
        onChangeText={(v) => setField("city", v)}
      />
      <AppInput
        compact
        label="District *"
        value={profile.district}
        editable={isEditing}
        onChangeText={(v) => setField("district", v)}
      />
      <AppInput
        compact
        label="State *"
        value={profile.state}
        editable={isEditing}
        onChangeText={(v) => setField("state", v)}
      />
      <AppInput
        compact
        label="Pincode"
        value={profile.pincode}
        editable={isEditing}
        keyboardType="number-pad"
        maxLength={6}
        onChangeText={(v) => setField("pincode", digitsOnly(v))}
      />
      <AppInput
        compact
        label="Landmark"
        value={profile.landmark}
        editable={isEditing}
        onChangeText={(v) => setField("landmark", v)}
      />
      <Pressable
        style={styles.checkboxRow}
        onPress={() => isEditing && setField("permanentSameAsLocal", !profile.permanentSameAsLocal)}
        disabled={!isEditing}
      >
        <Ionicons
          name={profile.permanentSameAsLocal ? "checkbox" : "square-outline"}
          size={18}
          color={profile.permanentSameAsLocal ? Colors.mainColour1 : Colors.gray400}
        />
        <AppText style={styles.checkboxLabel} color={Colors.gray600}>
          Click me if Permanent address is same
        </AppText>
      </Pressable>
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  checkboxLabel: { fontSize: Fonts.bodySm, flex: 1 },
});
