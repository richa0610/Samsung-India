import * as ImagePicker from "expo-image-picker";
import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { Alert } from "react-native";

import { ApiError, TrainerProfile, fetchTrainerProfile, updateTrainerProfile, uploadTrainerPhoto } from "@/api/trainerProfile";
import { useAuth } from "@/hooks/useAuth";
import { ProfileSectionKey, PROFILE_SECTION_FIELDS } from "./types";
import { sanitizeProfileSection, validateProfileSection } from "./sanitizeProfile";

const EMPTY_EDITING: Record<ProfileSectionKey, boolean> = {
  personal: false,
  address: false,
  documents: false,
  social: false,
  official: false,
  security: false,
};

const MAX_PHOTO_BYTES = 5 * 1024 * 1024;

export function useTrainerProfileForm() {
  const { adminToken } = useAuth();
  const [profile, setProfile] = useState<TrainerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(EMPTY_EDITING);
  const [savingSection, setSavingSection] = useState<ProfileSectionKey | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const load = useCallback(async () => {
    if (!adminToken) return;
    setLoading(true);
    try {
      setProfile(await fetchTrainerProfile(adminToken));
    } finally {
      setLoading(false);
    }
  }, [adminToken]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const setField = <K extends keyof TrainerProfile>(key: K, value: TrainerProfile[K]) => {
    setProfile((current) => (current ? { ...current, [key]: value } : current));
  };

  const toggleEdit = (section: ProfileSectionKey) => {
    setEditing((current) => ({ ...current, [section]: !current[section] }));
  };

  const saveSection = async (section: ProfileSectionKey) => {
    if (!adminToken || !profile) return;

    const validationError = validateProfileSection(section, profile);
    if (validationError) {
      setNotice(validationError);
      return;
    }
    const sanitized = sanitizeProfileSection(section, profile);
    setProfile(sanitized);

    setSavingSection(section);
    setNotice(null);
    try {
      const keys = PROFILE_SECTION_FIELDS[section] as (keyof TrainerProfile)[];
      const payload: Partial<TrainerProfile> = {};
      keys.forEach((key) => {
        (payload as Record<string, unknown>)[key] = sanitized[key];
      });
      const updated = await updateTrainerProfile(adminToken, payload);
      setProfile(updated);
      setEditing((current) => ({ ...current, [section]: false }));
    } catch {
      setNotice("Couldn't save your changes. Please try again.");
    } finally {
      setSavingSection(null);
    }
  };

  const handlePickPhoto = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Allow photo library access to set a profile picture.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.8,
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (result.canceled || !result.assets?.[0]) return;

    const asset = result.assets[0];
    if (asset.fileSize && asset.fileSize > MAX_PHOTO_BYTES) {
      Alert.alert("Image too large", "Please choose an image smaller than 5MB.");
      return;
    }
    if (!adminToken) return;

    setUploadingPhoto(true);
    try {
      const extension = asset.uri.split(".").pop()?.toLowerCase() || "jpg";
      const type =
        asset.mimeType ??
        (extension === "png" ? "image/png" : extension === "webp" ? "image/webp" : "image/jpeg");
      const updated = await uploadTrainerPhoto(adminToken, {
        uri: asset.uri,
        name: `profile.${extension}`,
        type,
      });
      // The server saves every re-upload under the same filename, so the
      // resolved media URL would otherwise be identical to before and the
      // avatar would keep showing its cached copy of the old photo - see
      // the same fix on the trainee side (useProfile.ts). The media route
      // ignores unknown query params, so this only affects display.
      setProfile(
        updated.profilePicture
          ? { ...updated, profilePicture: `${updated.profilePicture}?v=${Date.now()}` }
          : updated,
      );
    } catch (err) {
      Alert.alert(
        "Upload failed",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setUploadingPhoto(false);
    }
  };

  return {
    profile,
    loading,
    editing,
    savingSection,
    notice,
    uploadingPhoto,
    setField,
    toggleEdit,
    saveSection,
    handlePickPhoto,
  };
}

export type TrainerProfileForm = ReturnType<typeof useTrainerProfileForm>;
