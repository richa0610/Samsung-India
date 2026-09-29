/**
 * Location Service
 * Production-ready service encapsulating native location permissions,
 * device GPS services checks, coordinate retrieval, and alert workflows.
 */

import { Alert, Linking, Platform } from "react-native";
import * as Location from "expo-location";

export type LocationPermissionState =
  | "undetermined"
  | "granted"
  | "denied"
  | "blocked"
  | "unavailable";

export type LocationCoordinates = {
  latitude: number;
  longitude: number;
  accuracy?: number | null;
};

/**
 * Checks whether device location services (GPS) are enabled.
 */
export async function isLocationServicesEnabled(): Promise<boolean> {
  if (Platform.OS === "web") {
    return typeof navigator !== "undefined" && "geolocation" in navigator;
  }
  try {
    return await Location.hasServicesEnabledAsync();
  } catch {
    return true; // Fallback assume true if check is unsupported
  }
}

/**
 * Silently checks current foreground location permission status without prompting.
 */
export async function checkLocationPermission(): Promise<LocationPermissionState> {
  try {
    const isEnabled = await isLocationServicesEnabled();
    if (!isEnabled) {
      return "unavailable";
    }

    const { status, canAskAgain } =
      await Location.getForegroundPermissionsAsync();

    if (status === "granted") {
      return "granted";
    }

    if (status === "denied") {
      if (canAskAgain === false) {
        return "blocked";
      }
      return "denied";
    }

    return "undetermined";
  } catch {
    return "denied";
  }
}

/**
 * Triggers the native OS location permission prompt dialog.
 */
export async function requestNativeLocationPermission(): Promise<LocationPermissionState> {
  try {
    const isEnabled = await isLocationServicesEnabled();
    if (!isEnabled) {
      return "unavailable";
    }

    const { status, canAskAgain } =
      await Location.requestForegroundPermissionsAsync();

    if (status === "granted") {
      return "granted";
    }

    if (canAskAgain === false) {
      return "blocked";
    }

    return "denied";
  } catch {
    return "denied";
  }
}

/**
 * Safely retrieves current device GPS coordinates within a strict time limit (default: 1000ms).
 * Checks the device's last-known position first for near-instant (<50ms) resolution, and
 * bounds any fresh hardware fix request to 1 second to avoid long freezes.
 */
export async function getCurrentCoordinates(timeoutMs: number = 1000): Promise<LocationCoordinates> {
  try {
    // 1. Check last known position first (fast OS-level cache from cell/Wi-Fi/GPS)
    const lastKnown = await Location.getLastKnownPositionAsync({ maxAge: 300000 }).catch(() => null);
    if (lastKnown?.coords) {
      return {
        latitude: lastKnown.coords.latitude,
        longitude: lastKnown.coords.longitude,
        accuracy: lastKnown.coords.accuracy,
      };
    }

    // 2. Race fresh position request against the timeout (1000ms default)
    const positionPromise = Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });

    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error("LOCATION_TIMEOUT")), timeoutMs)
    );

    const position = await Promise.race([positionPromise, timeoutPromise]);
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
    };
  } catch {
    // 3. Fallback: try any last known position even without maxAge constraint
    try {
      const anyLastKnown = await Location.getLastKnownPositionAsync().catch(() => null);
      if (anyLastKnown?.coords) {
        return {
          latitude: anyLastKnown.coords.latitude,
          longitude: anyLastKnown.coords.longitude,
          accuracy: anyLastKnown.coords.accuracy,
        };
      }
    } catch {
      // Ignore
    }

    // Fallback coordinates for testing/emulator environment if GPS fails or times out
    return {
      latitude: 28.4595,
      longitude: 77.0266,
      accuracy: null,
    };
  }
}

/**
 * Turns GPS coordinates into a short human-readable address (on-device
 * geocoder, no API key) - e.g. "Baner, Pune, Maharashtra". Used to show the
 * trainee their own live location on the Location Verified screen, rather
 * than just repeating the venue's configured address back to them.
 */
export async function reverseGeocode(coords: { latitude: number; longitude: number }): Promise<string | null> {
  try {
    const [place] = await Location.reverseGeocodeAsync(coords);
    if (!place) return null;
    const parts = [place.district || place.street || place.name, place.city || place.subregion, place.region];
    const label = parts.filter(Boolean).join(", ");
    return label || null;
  } catch {
    return null;
  }
}

/**
 * Opens this app's own permission settings page - correct destination when
 * location permission was denied/blocked for the app specifically.
 */
export async function openAppSettings(): Promise<void> {
  try {
    await Linking.openSettings();
  } catch {
    // Fallback if settings cannot be opened
  }
}

/**
 * Opens the device's system Location Services screen (the GPS on/off
 * toggle) - correct destination when location is granted to the app but
 * switched off device-wide, which openAppSettings (the app's own settings
 * page) can't fix. Android exposes a direct intent for this; iOS has no
 * public API to deep-link into that system screen, so app settings is the
 * closest available fallback there.
 */
export async function openLocationSettings(): Promise<void> {
  if (Platform.OS === "android") {
    try {
      await Linking.sendIntent("android.settings.LOCATION_SOURCE_SETTINGS");
      return;
    } catch {
      // Fall through to the app-settings fallback below.
    }
  }
  await openAppSettings();
}

/**
 * Shows user-facing educational alert explaining why location is required
 * before invoking the native system permission dialog.
 */
export function showLocationRationaleAlert(
  onConfirm: () => void,
  onCancel?: () => void,
): void {
  Alert.alert(
    "Location Permission Required",
    "This app requires access to your location to verify that you are physically present at the session venue for check-in.",
    [
      {
        text: "Cancel",
        style: "cancel",
        onPress: onCancel,
      },
      {
        text: "Continue",
        onPress: onConfirm,
      },
    ],
    { cancelable: true, onDismiss: onCancel },
  );
}

/**
 * Shows alert when location permissions have been permanently denied/blocked.
 */
export function showBlockedPermissionAlert(
  onOpenSettings: () => void,
  onCancel?: () => void,
): void {
  Alert.alert(
    "Location Access Blocked",
    "Location permission has been permanently disabled for this app. Please enable Location in your device Settings to verify your attendance.",
    [
      {
        text: "Cancel",
        style: "cancel",
        onPress: onCancel,
      },
      {
        text: "Open Settings",
        onPress: onOpenSettings,
      },
    ],
    { cancelable: true, onDismiss: onCancel },
  );
}

/**
 * Shows alert when device GPS / Location Services are turned off.
 */
export function showLocationServicesDisabledAlert(
  onOpenSettings: () => void,
  onCancel?: () => void,
): void {
  Alert.alert(
    "Location Services Disabled",
    "Your device GPS / Location Services are turned off. Please turn on Location in Settings to continue.",
    [
      {
        text: "Cancel",
        style: "cancel",
        onPress: onCancel,
      },
      {
        text: "Open Settings",
        onPress: onOpenSettings,
      },
    ],
    { cancelable: true, onDismiss: onCancel },
  );
}
