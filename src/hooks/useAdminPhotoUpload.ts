import * as ImagePicker from "expo-image-picker";
import { useState } from "react";
import { Alert } from "react-native";
import ImageCropPicker from "react-native-image-crop-picker";

import { ApiError, uploadTrainerPhoto } from "@/api/trainerProfile";
import { useAuth } from "@/hooks/useAuth";

const MAX_PHOTO_BYTES = 5 * 1024 * 1024;

/** Tap-the-avatar flow for admin/trainer accounts: pick a photo, crop it, upload
 *  it, and refresh the avatar everywhere - same steps as the trainer's profile
 *  screen, without opening it. */
export function useAdminPhotoUpload() {
  const { adminToken, updateAdminPhoto } = useAuth();
  const [uploading, setUploading] = useState(false);

  const pickAndUpload = async () => {
    if (!adminToken || uploading) return;

    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Allow photo library access to set a profile picture.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.8, allowsEditing: false });
    if (result.canceled || !result.assets?.[0]) return;

    let cropped;
    try {
      cropped = await ImageCropPicker.openCropper({
        path: result.assets[0].uri,
        mediaType: "photo",
        width: 512,
        height: 512,
        cropperToolbarTitle: "Crop Photo",
        cropperCancelText: "Cancel",
        cropperChooseText: "Done",
        compressImageQuality: 0.8,
        freeStyleCropEnabled: false,
      });
    } catch (err) {
      if ((err as { code?: string } | null)?.code === "E_PICKER_CANCELLED") return;
      Alert.alert("Crop failed", "Couldn't crop that photo. Please try again.");
      return;
    }

    if (cropped.size > MAX_PHOTO_BYTES) {
      Alert.alert("Image too large", "Please choose an image smaller than 5MB.");
      return;
    }

    setUploading(true);
    try {
      const extension = cropped.mime.split("/").pop() || "jpg";
      const uri = cropped.path.startsWith("file://") ? cropped.path : `file://${cropped.path}`;
      const updated = await uploadTrainerPhoto(adminToken, { uri, name: `profile.${extension}`, type: cropped.mime });
      // Re-uploads reuse one filename on the server, so bust the image cache or
      // the avatar would keep showing the old photo.
      if (updated.profilePicture) updateAdminPhoto(`${updated.profilePicture}?v=${Date.now()}`);
    } catch (err) {
      Alert.alert("Upload failed", err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return { pickAndUpload, uploading };
}
