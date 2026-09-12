import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Alert } from "react-native";

import { ApiError, uploadTraineePhoto } from "@/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { DetailItem, MAX_PHOTO_BYTES, locationLabel } from "./constants";

export function useProfile() {
  const router = useRouter();
  const { trainee, token, logout, setSession } = useAuth();
  const [editVisible, setEditVisible] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleLogout = () => {
    logout();
    router.replace("/");
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
    if (!token) return;

    setUploading(true);
    try {
      const extension = asset.uri.split(".").pop()?.toLowerCase() || "jpg";
      const type =
        asset.mimeType ??
        (extension === "png" ? "image/png" : extension === "webp" ? "image/webp" : "image/jpeg");
      const updated = await uploadTraineePhoto(token, {
        uri: asset.uri,
        name: `profile.${extension}`,
        type,
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
    handleLogout,
    handlePickPhoto,
    handleTabSelect,
    personalDetails,
    organizationDetails,
    sessionPillLabel,
  };
}
