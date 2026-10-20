import * as ImagePicker from "expo-image-picker";
import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, BackHandler } from "react-native";
import ImageCropPicker from "react-native-image-crop-picker";

import { ApiError, uploadTraineePhoto } from "@/api/auth";
import {
  CurrentSession,
  getCachedCurrentSession,
  getCurrentSession,
  isSessionLive,
  setCachedCurrentSession,
} from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { canNavigate } from "@/utils/navigationGuard";
import { DetailItem, MAX_PHOTO_BYTES, placeName, shownValue } from "./constants";

export function useProfile() {
  const router = useRouter();
  const { trainee, token, logout, setSession } = useAuth();
  const [session, setSessionState] = useState<CurrentSession | null>(() => getCachedCurrentSession(token));
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
    if (canNavigate()) router.replace("/");
  };

  // Hardware/gesture back asks for confirmation instead of navigating
  // anywhere - same popup and destination as the header's power button, on
  // every trainee tab (Home/Dashboard/Rank/Profile) uniformly.
  useFocusEffect(
    useCallback(() => {
      const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
        requestLogout();
        return true;
      });
      return () => subscription.remove();
    }, []),
  );

  useFocusEffect(
    useCallback(() => {
      if (!token) {
        setSessionState(null);
        return;
      }
      getCurrentSession(token)
        .then((s) => {
          setSessionState(s);
          setCachedCurrentSession(token, s);
        })
        .catch(() => setSessionState(null));
    }, [token]),
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
    // Guards against a real Fabric crash ("child already has a parent")
    // from firing a second replace() before the previous tab's screen
    // transition has finished mounting - see utils/navigationGuard.ts.
    if (!canNavigate()) return;
    if (tab === "home") {
      router.replace("/session_detail");
    } else if (tab === "dashboard") {
      router.replace("/trainee_dashboard");
    } else if (tab === "rank") {
      router.replace({
        pathname: "/quiz_leaderboard",
        params: { conferenceUid: session?.conferenceUid ?? "" },
      });
    }
  };

  // The trainee's own saved values - "--" where one is empty, never a made-up value (user, 2026-10-13).
  const personalDetails: DetailItem[] = [
    { icon: "call", label: "Mobile", value: shownValue(trainee?.phone) },
    { icon: "mail", label: "Email", value: shownValue(trainee?.email) },
    { icon: "briefcase", label: "Designation", value: shownValue(trainee?.designation) },
    { icon: "card", label: "Employee ID", value: shownValue(trainee?.employee_id) },
    { icon: "location", label: "Zone", value: shownValue(trainee?.zone) },
    { icon: "map", label: "Region", value: shownValue(trainee?.region) },
  ];

  const organizationDetails: DetailItem[] = [
    { icon: "person", label: "Reporting Manager", value: shownValue(trainee?.supervisorName) },
    { icon: "ribbon", label: "Manager's Designation", value: shownValue(trainee?.supervisorDesignation) },
  ];

  // The saved district and state ("" - no pill - when neither is saved).
  const sessionPillLabel = [placeName(trainee?.district), placeName(trainee?.state)].filter(Boolean).join(", ");
  const isTrainingLive = isSessionLive(session);

  return {
    trainee,
    session,
    isTrainingLive,
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
