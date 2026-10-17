import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { digitsOnly } from "@/utils/validation";
import { TrainerProfileForm } from "./useTrainerProfileForm";
import { ProfileSection } from "./ProfileSection";

export function LocalAddressSection({ form }: { form: TrainerProfileForm }) {
  const { profile, editing, savingSection, setField, toggleEdit, saveSection } = form;
  if (!profile) return null;
  const isEditing = editing.address;
  const sameAsLocal = profile.permanentSameAsLocal;
  // While "same as local" is on, the Permanent fields only ever *display*
  // the Local ones live (so editing Local visibly updates Permanent too) -
  // sanitizeProfileSection is what actually copies the values into
  // permanentCity/etc. at save time, not this render.
  const permanentEditable = isEditing && !sameAsLocal;

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
        label="City"
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

      <View style={styles.divider} />

      <AppText style={styles.subTitle} weight={FontWeight.semiBold}>
        Permanent Address
      </AppText>

      <AppInput
        compact
        label="City"
        value={sameAsLocal ? profile.city : profile.permanentCity}
        editable={permanentEditable}
        onChangeText={(v) => setField("permanentCity", v)}
      />
      <AppInput
        compact
        label="District"
        value={sameAsLocal ? profile.district : profile.permanentDistrict}
        editable={permanentEditable}
        onChangeText={(v) => setField("permanentDistrict", v)}
      />
      <AppInput
        compact
        label="State"
        value={sameAsLocal ? profile.state : profile.permanentState}
        editable={permanentEditable}
        onChangeText={(v) => setField("permanentState", v)}
      />
      <AppInput
        compact
        label="Pincode"
        value={sameAsLocal ? profile.pincode : profile.permanentPincode}
        editable={permanentEditable}
        keyboardType="number-pad"
        maxLength={6}
        onChangeText={(v) => setField("permanentPincode", digitsOnly(v))}
      />
      <AppInput
        compact
        label="Landmark"
        value={sameAsLocal ? profile.landmark : profile.permanentLandmark}
        editable={permanentEditable}
        onChangeText={(v) => setField("permanentLandmark", v)}
      />
    </ProfileSection>
  );
}

const styles = StyleSheet.create({
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  checkboxLabel: { fontSize: Fonts.bodySm, flex: 1 },
  divider: { height: 1, backgroundColor: Colors.gray100, marginVertical: 14 },
  subTitle: { fontSize: Fonts.body, marginBottom: 10 },
});
