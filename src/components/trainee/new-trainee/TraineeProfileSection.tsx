import { useState } from "react";
import { ActivityIndicator, Alert, Image, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { DateTimeField } from "@/components/training/add-training/DateTimeField";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";
import { AGENCY_OPTIONS, DESIGNATION_OPTIONS, GENDER_OPTIONS } from "./constants";
import { NewTraineeForm } from "./useNewTraineeForm";

export function TraineeProfileSection({ form }: { form: NewTraineeForm }) {
  const [picking, setPicking] = useState(false);

  const handlePickPhoto = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Allow photo library access to set a profile picture.");
      return;
    }
    setPicking(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 0.8,
        allowsEditing: true,
        aspect: [1, 1],
      });
      if (!result.canceled && result.assets?.[0]) {
        form.setProfilePhoto(result.assets[0].uri);
      }
    } finally {
      setPicking(false);
    }
  };

  return (
    <AppCard style={styles.card}>
      <SectionTitle index={3} title="Trainee Profile" icon="person-outline" />

      <View style={styles.photoBlock}>
        <AppText style={styles.photoLabel} color={Colors.gray600}>Profile Photo</AppText>
        <View style={styles.avatarWrap}>
          <Image
            source={form.profilePhoto ? { uri: form.profilePhoto } : require("@/assets/images/profile.webp")}
            style={styles.avatar}
          />
        </View>
        <Pressable style={styles.uploadButton} onPress={handlePickPhoto} disabled={picking}>
          {picking ? (
            <ActivityIndicator size="small" color={Colors.gray600} />
          ) : (
            <Ionicons name="cloud-upload-outline" size={16} color={Colors.gray600} />
          )}
          <AppText style={styles.uploadText} color={Colors.gray600}>Tap To Upload (PNG, JPG)</AppText>
        </Pressable>
      </View>

      <AppInput
        label="Trainee UID *"
        placeholder="Enter Trainee UID"
        icon="briefcase-outline"
        autoCapitalize="characters"
        value={form.traineeUid}
        onChangeText={form.setTraineeUid}
      />
      <SearchableSelect
        label="Agency ID (Optional)"
        placeholder="Select if applicable"
        icon="briefcase-outline"
        value={form.agencyId}
        options={AGENCY_OPTIONS}
        onSelect={(option) => form.setAgencyId(option.value)}
      />
      <AppInput
        label="Full Name *"
        placeholder="Enter Full Name"
        icon="person-outline"
        autoCapitalize="words"
        value={form.fullName}
        onChangeText={form.setFullName}
      />
      <SearchableSelect
        label="Designation"
        required
        placeholder="e.g. Sales Executive"
        icon="briefcase-outline"
        value={form.designation}
        options={DESIGNATION_OPTIONS}
        onSelect={(option) => form.setDesignation(option.value)}
      />
      <SearchableSelect
        label="Gender"
        required
        placeholder="Select Gender"
        icon="male-female-outline"
        value={form.gender}
        options={GENDER_OPTIONS}
        onSelect={(option) => form.setGender(option.value)}
      />
      <DateTimeField label="Date of Birth" mode="date" value={form.dob} onChange={form.setDob} />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  photoBlock: { alignItems: "center", marginBottom: Spacing.lg },
  photoLabel: { fontSize: Fonts.body, marginBottom: Spacing.sm },
  avatarWrap: {
    width: 100,
    height: 100,
    borderRadius: 44,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    marginBottom: Spacing.md,
  },
  avatar: { width: 88, height: 88, borderRadius: 44 },
  uploadButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    width: "100%",
    height: 44,
    borderRadius: Radius.xl,
    borderWidth: 1,
    borderColor: Colors.gray200,
    backgroundColor: Colors.gray100,
  },
  uploadText: { fontSize: Fonts.bodySm },
});
