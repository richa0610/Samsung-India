import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, ImageSourcePropType } from "react-native";
import { useRouter } from "expo-router";

import { ApiError, VerifyLocationResult, secureCheckIn, verifyLocation } from "@/api/attendance";
import { setAttendanceState, setPendingCheckIn, setSessionFlowState } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { useLocationPermission } from "@/hooks/useLocationPermission";
import { reverseGeocode } from "@/services/locationService";

export type SecureCheckInStep =
  | "locating"
  | "location-verified"
  | "security-checkin"
  | "submitting"
  | "granted"
  | "error";

type SecureCheckInParams = {
  conferenceUid: string;
  mode?: "entry" | "attendance";
};

export function useSecureCheckIn(params: SecureCheckInParams) {
  const router = useRouter();
  const { token } = useAuth();
  const isEntryMode = params.mode !== "attendance";

  const {
    permissionState,
    coords: locationCoords,
    loading: locationLoading,
    error: locationError,
    requestLocationWithRationale,
    openSettings,
  } = useLocationPermission();

  const [step, setStep] = useState<SecureCheckInStep>("locating");
  const [error, setError] = useState<string | null>(null);
  const [activeCoords, setActiveCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationResult, setLocationResult] = useState<VerifyLocationResult | null>(null);
  const [verifiedAt, setVerifiedAt] = useState<Date | null>(null);
  const [liveLocationLabel, setLiveLocationLabel] = useState<string | null>(null);

  const startLocationVerification = useCallback(async () => {
    if (!token || !params.conferenceUid) return;
    setStep("locating");
    setError(null);

    const { coords, status, error: permError } = await requestLocationWithRationale();

    if (status === "granted" && coords) {
      setActiveCoords(coords);
      setLiveLocationLabel(null);
      // Best-effort - the on-device geocoder can be slow/unavailable, and the
      // trainee's own location label is a nice-to-have, not blocking.
      reverseGeocode(coords).then(setLiveLocationLabel);
      try {
        const result = await verifyLocation(token, params.conferenceUid, coords.latitude, coords.longitude);
        setLocationResult(result);
        // Geofenced session, trainee outside the radius - hard stop here (the
        // backend enforces it again at submit, this is the friendly pre-check).
        if (result.withinRadius === false) {
          const radius = result.radiusMeters ?? 100;
          const away =
            result.distanceMeters != null ? ` (about ${Math.round(result.distanceMeters)} m away)` : "";
          Alert.alert(
            "You're too far from the venue",
            `Please come within the venue radius of ${radius} m to mark your attendance.${
              away ? `\n\nYou're currently${away}.` : ""
            }`,
          );
          setError(
            `You're not at the training venue${away}. Move within ${radius} m and try again.`,
          );
          setStep("error");
          return;
        }
        setVerifiedAt(new Date());
        setStep("location-verified");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Couldn't verify your location with the venue.");
        setStep("error");
      }
    } else {
      setError(
        permError ||
          (status === "blocked"
            ? "Location permission is permanently blocked. Please enable it in Settings."
            : status === "unavailable"
              ? "Device GPS is disabled. Please turn on Location in Settings."
              : "Location access was denied. Location verification is required for check-in."),
      );
      setStep("error");
    }
  }, [token, params.conferenceUid, requestLocationWithRationale]);

  const hasInitiatedRef = useRef(false);

  useEffect(() => {
    if (!hasInitiatedRef.current) {
      hasInitiatedRef.current = true;
      startLocationVerification();
    }
  }, [startLocationVerification]);

  const handleProceedFromCheckIn = async (photoSource: ImageSourcePropType) => {
    const currentCoords = activeCoords || locationCoords;
    const photoUri =
      typeof photoSource === "object" && photoSource && "uri" in photoSource
        ? (photoSource as { uri: string }).uri
        : "checkin.jpg";

    if (isEntryMode) {
      // Carry the trainee's location + photo forward to the secure check-in
      // endpoint. This happens for every session now, geofenced or not - a
      // geofenced one is additionally hard-blocked outside the radius (that
      // `false` case already bailed above); a non-geofenced one just records
      // the coordinates alongside the attendance row.
      if (currentCoords) {
        setPendingCheckIn({
          latitude: currentCoords.latitude,
          longitude: currentCoords.longitude,
          photoUri,
        });
      }
      setSessionFlowState("CAMERA_VERIFIED");
      router.replace({ pathname: "/session_detail", params: { flow: "CAMERA_VERIFIED" } });
      return;
    }

    if (!token || !params.conferenceUid || !currentCoords) return;
    setStep("submitting");
    setError(null);
    try {
      await secureCheckIn(token, {
        conferenceUid: params.conferenceUid,
        latitude: currentCoords.latitude,
        longitude: currentCoords.longitude,
        photo: { uri: photoUri, name: "checkin.jpg", type: "image/jpeg" },
      });
      setAttendanceState("ATTENDANCE_RECORDED");
      setStep("granted");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Couldn't submit your check-in.";
      // Backend's geofence rejection ("...Move within N m to check in.") -
      // surface it as a popup so the trainee sees it immediately, not just on
      // the error screen behind the camera.
      if (err instanceof ApiError && /move within/i.test(err.message)) {
        Alert.alert("You're too far from the venue", err.message);
      }
      setError(message);
      setStep("error");
    }
  };

  return {
    router,
    step,
    setStep,
    error,
    locationResult,
    verifiedAt,
    liveLocationLabel,
    permissionState,
    locationLoading,
    locationError,
    openSettings,
    startLocationVerification,
    handleProceedFromCheckIn,
  };
}
