import { useCallback, useEffect, useState } from "react";
import { Alert } from "react-native";

import { ApiError, CheckInSettings, fetchCheckInSettings, updateCheckInSettings } from "@/api/admin";
import { useAuth } from "@/hooks/useAuth";

/** The tenant's check-in settings for the admin panel. Only a Super Admin can read them, so
 *  `settings` stays null for everyone else (the server refuses them) and the control isn't shown. */
export function useCheckInSettings() {
  const { adminToken } = useAuth();
  const [settings, setSettings] = useState<CheckInSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!adminToken) return;
    let active = true;
    fetchCheckInSettings(adminToken)
      .then((next) => active && setSettings(next))
      .catch(() => active && setSettings(null));
    return () => {
      active = false;
    };
  }, [adminToken]);

  const save = useCallback(
    async (faceDetectionEnabled: boolean) => {
      if (!adminToken || !settings) return;
      const previous = settings;
      setSettings({ faceDetectionEnabled });
      setSaving(true);
      try {
        setSettings(await updateCheckInSettings(adminToken, { faceDetectionEnabled }));
      } catch (err) {
        setSettings(previous);
        Alert.alert("Couldn't save the setting", err instanceof ApiError ? err.message : "Please try again.");
      } finally {
        setSaving(false);
      }
    },
    [adminToken, settings],
  );

  /** Turning the face check off is confirmed first - it removes a security step for every trainee. */
  const setFaceDetection = useCallback(
    (enabled: boolean) => {
      if (enabled) {
        save(true);
        return;
      }
      Alert.alert(
        "Turn off face detection?",
        "Trainees in this company will just capture a photo at check-in, without the face check.",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Turn off", style: "destructive", onPress: () => save(false) },
        ],
      );
    },
    [save],
  );

  return { settings, saving, setFaceDetection };
}
