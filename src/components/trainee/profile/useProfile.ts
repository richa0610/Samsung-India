import * as ImagePicker from "expo-image-picker";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, BackHandler } from "react-native";
import ImageCropPicker from "react-native-image-crop-picker";

import { ApiError, uploadTraineePhoto } from "@/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { DetailItem, MAX_PHOTO_BYTES, locationLabel } from "./constants";

export function useProfile() {
  const router = useRouter();
  const { trainee, token, logout, setSession } = useAuth();
  const [editVisible, setEditVisible] = useState(false);
  const [uploading, setUploading] = useState(false);
  // Same confirm-before-logout flow as the trainer's dashboard/profile
  // power button - opening the popup is separate from actually logging
  // out, which only happens on confirm.
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  const requestLogout = () => setConfirmLogoutOpen(true);
  const cancelLogout = () => setConfirmLogoutOpen(false);
  const confirmLogout = () => {
    setConfirmLogoutOpen(false);
    logout();
    router.replace("/");
  };

  // Tabs replace() each other in place rather than stacking, so there's no
  // separate Home entry left underneath this one to pop back into -
  // default hardware back would skip straight past Home to whatever came
  // before the session flow. Force it through the same replace() the Home
  // tab itself uses, matching the Rank/Dashboard pages' identical fix.
  useFocusEffect(
    useCallback(() => {
      const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
        router.replace("/session_detail");
        return true;
      });
      return () => subscription.remove();
    }, [router]),
  );

  const handlePickPhoto = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission needed", "Allow photo library access to set a profile picture.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.8,
      // Cropping now happens in the step below, via a dedicated cropper
      // that gives a consistent Cancel/Rotate/Done screen on every device -
      // the OS's own built-in editor (previously used here) looks
      // completely different depending on the phone's manufacturer.
      allowsEditing: false,
    });
    if (result.canceled || !result.assets?.[0]) return;

    const asset = result.assets[0];

    let cropped;
    try {
      cropped = await ImageCropPicker.openCropper({
        path: asset.uri,
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
      // User backed out of the crop screen - not a failure, just no photo
      // picked this time.
      if ((err as { code?: string } | null)?.code === "E_PICKER_CANCELLED") return;
      Alert.alert("Crop failed", "Couldn't crop that photo. Please try again.");
      return;
    }

    if (cropped.size > MAX_PHOTO_BYTES) {
      Alert.alert("Image too large", "Please choose an image smaller than 5MB.");
      return;
    }
    if (!token) return;

    setUploading(true);
    try {
      const extension = cropped.mime.split("/").pop() || "jpg";
      const uri = cropped.path.startsWith("file://") ? cropped.path : `file://${cropped.path}`;
      const updated = await uploadTraineePhoto(token, {
        uri,
        name: `profile.${extension}`,
        type: cropped.mime,
      });
      // The server saves every re-upload under the same filename
      // (traineeUid.ext), so profilePhoto's value - and therefore the
      // resolved media URL - would otherwise be byte-identical to before,
      // and the avatar <Image> would keep showing its cached copy of the
      // old photo. A cache-busting query param forces it to refetch. This
      // only touches the in-memory copy set below, not what's persisted -
      // the media route already ignores unknown query params.
      const bustedTrainee = updated.profilePhoto
        ? { ...updated, profilePhoto: `${updated.profilePhoto}?v=${Date.now()}` }
        : updated;
      setSession({ access_token: token, token_type: "bearer", trainee: bustedTrainee });
    } catch (err) {
      Alert.alert(
        "Upload failed",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setUploading(false);
    }
  };

  const handleTabSelect = (tab: TraineeTab) => {
    if (tab === "home") {
      router.replace("/session_detail");
    } else if (tab === "dashboard") {
      router.replace("/trainee_dashboard");
    } else if (tab === "rank") {
      router.replace("/quiz_leaderboard");
    }
  };

  // Personal Details Rows with robust backend property fallback bindings
  const personalDetails: DetailItem[] = [
    { icon: "call", label: "Mobile", value: trainee?.phone ? String(trainee.phone) : "8750574444" },
    { icon: "mail", label: "Email", value: trainee?.email || "anandkumar@quess.com" },
    { icon: "briefcase", label: "Designation", value: trainee?.designation || "SEC" },
    { icon: "card", label: "Employee ID", value: trainee?.employee_id || "SOUTH1234" },
    {
      icon: "location",
      label: "Work Zone",
      value: trainee?.workZone || (trainee?.state ? locationLabel(trainee.state, trainee.district) : "SOUTH"),
    },
  ];

  // Organization Details Rows with backend property fallback bindings
  const organizationDetails: DetailItem[] = [
    { icon: "person", label: "Reporting Manager", value: trainee?.supervisorName || "ANAND ROY" },
    { icon: "call", label: "Department Support", value: trainee?.departmentSupport || "8569741259" },
    { icon: "business", label: "Department", value: trainee?.department || "SALES HEAD" },
  ];

  const sessionPillLabel =
    trainee?.sessionCode || (trainee?.state ? locationLabel(trainee.state, trainee.district) : "SOUTH 12234");

  return {
    trainee,
    uploading,
    editVisible,
    setEditVisible,
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
    handlePickPhoto,
    handleTabSelect,
    personalDetails,
    organizationDetails,
    sessionPillLabel,
  };
}
