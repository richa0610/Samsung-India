import { ScrollView, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppButton from "@/components/ui/AppButton";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import PersonalDetails from "@/components/registration/PersonalDetails";
import ProfessionalDetails from "@/components/registration/ProfessionalDetails";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { useEditProfileForm } from "@/hooks/useEditProfileForm";

type EditProfileSheetProps = {
  visible: boolean;
  onClose: () => void;
};

export default function EditProfileSheet({ visible, onClose }: EditProfileSheetProps) {
  const { control, errors, setValue, onSubmit, loading, error, lockedFields } =
    useEditProfileForm({ onSuccess: onClose });

  return (
    <AppModal
      visible={visible}
      title="Edit Profile"
      subtitle="Update your credentials"
      onClose={onClose}
      position="bottom"
      showCloseButton
      contentStyle={styles.sheet}
    >
      <View style={styles.divider} />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.formContent}>
        <PersonalDetails control={control} errors={errors} lockedFields={lockedFields} />
        <ProfessionalDetails
          control={control}
          setValue={setValue}
          errors={errors}
          lockedFields={lockedFields}
        />

        {error && <AppText style={styles.error}>{error}</AppText>}

        <AppButton
          title={loading ? "Saving..." : "Save Changes"}
          onPress={onSubmit}
          loading={loading}
          rightIcon={<Ionicons name="checkmark" color="#fff" size={18} />}
        />
      </ScrollView>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { paddingHorizontal: 20, paddingTop: 20, paddingBottom: 40, maxHeight: "85%" },
  formContent: { paddingBottom: 4 },
  divider: { height: 1, backgroundColor: Colors.inputColour2, marginVertical: 16 },
  error: { color: Colors.danger, fontSize: Fonts.bodySm, marginBottom: 12, textAlign: "center" },
});
