import { useCallback, useRef, useState } from "react";
import { useRouter } from "expo-router";
import { scanFromURLAsync, useCameraPermissions, type BarcodeScanningResult } from "expo-camera";
import * as ImagePicker from "expo-image-picker";

import { parseJoinCode } from "./parseJoinCode";

/**
 * Backs the in-app QR scanner (`app/scan.tsx`) - the participant entry
 * point. Reads a session QR with expo-camera, pulls the conference code
 * out of it, and hands off to the join screen (the same place a
 * `samsungindia://join/<code>` deep link lands, so the rest of the flow -
 * preview -> login/register -> session - is unchanged). The QR can be read
 * live from the camera or picked from the photo gallery (UPI-style).
 */
export function useQrScanner() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [error, setError] = useState<string | null>(null);
  const [decoding, setDecoding] = useState(false);
  const handled = useRef(false);

  const goToJoin = useCallback(
    (raw: string): boolean => {
      const code = parseJoinCode(raw);
      if (!code) return false;
      handled.current = true;
      router.replace({ pathname: "/join/[code]", params: { code } });
      return true;
    },
    [router],
  );

  const handleScanned = useCallback(
    (result: BarcodeScanningResult) => {
      if (handled.current) return;
      if (!goToJoin(result.data)) {
        setError("That doesn't look like a session QR code.");
      }
    },
    [goToJoin],
  );

  // Pick a screenshot / saved image of the QR from the photo library and
  // decode it - for a trainee who was sent the QR image rather than being in
  // front of the printed one. Doesn't need camera permission.
  const handlePickFromGallery = useCallback(async () => {
    if (handled.current || decoding) return;
    setError(null);

    const lib = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!lib.granted) {
      setError("Allow photo library access to pick a QR image.");
      return;
    }

    // No editing / re-encode - hand the original file to the decoder.
    const picked = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"] });
    if (picked.canceled || !picked.assets?.[0]) return;

    setDecoding(true);
    try {
      const scans = await scanFromURLAsync(picked.assets[0].uri, ["qr"]);
      const codes = scans.map((s) => s.data).filter(Boolean);
      const match = codes.map(parseJoinCode).find((c): c is string => !!c);

      if (match && goToJoin(match)) return;

      if (codes.length === 0) {
        setError("Couldn't detect a QR code in that image. Try a sharper or tighter-cropped screenshot.");
      } else {
        // A QR was read, it's just not a session link - show what it held.
        const seen = codes[0].length > 48 ? `${codes[0].slice(0, 48)}…` : codes[0];
        setError(`That QR isn't a session code (it holds "${seen}").`);
      }
    } catch (e) {
      setError("Couldn't read that image. Pick a PNG/JPG screenshot of the QR.");
      if (__DEV__) console.warn("[qr gallery] scanFromURLAsync failed:", e);
    } finally {
      setDecoding(false);
    }
  }, [decoding, goToJoin]);

  return {
    granted: permission?.granted ?? false,
    canAskAgain: permission?.canAskAgain ?? true,
    requestPermission,
    error,
    decoding,
    handleScanned,
    handlePickFromGallery,
    onClose: () => router.back(),
  };
}
