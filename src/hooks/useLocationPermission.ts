/**
 * useLocationPermission Hook
 * Reusable hook encapsulating location permission lifecycle, rationale prompts,
 * state management (granted, denied, blocked, unavailable), and GPS coordinate retrieval.
 */

import { useCallback, useRef, useState } from "react";
import {
  LocationCoordinates,
  LocationPermissionState,
  checkLocationPermission,
  getCurrentCoordinates,
  openAppSettings,
  requestNativeLocationPermission,
  showBlockedPermissionAlert,
  showLocationRationaleAlert,
  showLocationServicesDisabledAlert,
} from "@/services/locationService";

export type LocationPermissionResult = {
  coords: LocationCoordinates | null;
  status: LocationPermissionState;
  error?: string | null;
};

export function useLocationPermission() {
  const [permissionState, setPermissionState] =
    useState<LocationPermissionState>("undetermined");
  const [coords, setCoords] = useState<LocationCoordinates | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRequestingRef = useRef(false);

  /**
   * Prompts user with an educational rationale alert before triggering
   * the native OS location permission dialog.
   */
  const requestLocationWithRationale = useCallback(
    (): Promise<LocationPermissionResult> => {
      return new Promise(async (resolve) => {
        if (isRequestingRef.current) {
          return resolve({
            coords,
            status: permissionState,
            error: error ?? undefined,
          });
        }

        // 1. Check if permission is already granted silently
        const currentStatus = await checkLocationPermission();
        if (currentStatus === "granted") {
          setLoading(true);
          setError(null);
          try {
            const currentCoords = await getCurrentCoordinates();
            setCoords(currentCoords);
            setPermissionState("granted");
            setLoading(false);
            return resolve({ coords: currentCoords, status: "granted" });
          } catch {
            setLoading(false);
            setError("Failed to retrieve GPS location.");
            return resolve({
              coords: null,
              status: "granted",
              error: "Failed to retrieve GPS location.",
            });
          }
        }

        if (currentStatus === "blocked") {
          setPermissionState("blocked");
          showBlockedPermissionAlert(() => openAppSettings());
          setError(
            "Location permission is blocked. Please enable it in Settings.",
          );
          return resolve({
            coords: null,
            status: "blocked",
            error: "Location permission is blocked.",
          });
        }

        if (currentStatus === "unavailable") {
          setPermissionState("unavailable");
          showLocationServicesDisabledAlert(() => openAppSettings());
          setError(
            "Device location services are disabled. Please turn on GPS in Settings.",
          );
          return resolve({
            coords: null,
            status: "unavailable",
            error: "Device location services are disabled.",
          });
        }

        // 2. Show clear user-facing rationale before triggering native prompt
        showLocationRationaleAlert(
          async () => {
            isRequestingRef.current = true;
            setLoading(true);
            setError(null);

            try {
              const status = await requestNativeLocationPermission();
              setPermissionState(status);

              if (status === "granted") {
                const currentCoords = await getCurrentCoordinates();
                setCoords(currentCoords);
                setLoading(false);
                isRequestingRef.current = false;
                return resolve({ coords: currentCoords, status: "granted" });
              }

              if (status === "blocked") {
                setLoading(false);
                isRequestingRef.current = false;
                setError(
                  "Location permission is blocked. Please enable it in Settings.",
                );
                showBlockedPermissionAlert(() => openAppSettings());
                return resolve({
                  coords: null,
                  status: "blocked",
                  error: "Permission blocked.",
                });
              }

              if (status === "unavailable") {
                setLoading(false);
                isRequestingRef.current = false;
                setError(
                  "Device location services are disabled. Please turn on GPS in Settings.",
                );
                showLocationServicesDisabledAlert(() => openAppSettings());
                return resolve({
                  coords: null,
                  status: "unavailable",
                  error: "Location services disabled.",
                });
              }

              // status === "denied"
              setLoading(false);
              isRequestingRef.current = false;
              setError(
                "Location access was denied. Location verification is required for check-in.",
              );
              return resolve({
                coords: null,
                status: "denied",
                error: "Location access denied.",
              });
            } catch {
              setLoading(false);
              isRequestingRef.current = false;
              setError("An error occurred while requesting location access.");
              return resolve({
                coords: null,
                status: "denied",
                error: "Request failed.",
              });
            }
          },
          () => {
            // User cancelled rationale
            setError("Location permission is required to proceed with check-in.");
            resolve({
              coords: null,
              status: "denied",
              error: "Permission cancelled.",
            });
          },
        );
      });
    },
    [coords, permissionState, error],
  );

  /**
   * Direct retry handler without re-running rationale if already prompted.
   */
  const retryLocationRequest = useCallback(async (): Promise<LocationPermissionResult> => {
    if (permissionState === "blocked" || permissionState === "unavailable") {
      await openAppSettings();
      return { coords: null, status: permissionState };
    }
    return requestLocationWithRationale();
  }, [permissionState, requestLocationWithRationale]);

  return {
    permissionState,
    coords,
    loading,
    error,
    requestLocationWithRationale,
    retryLocationRequest,
    openSettings: openAppSettings,
  };
}
