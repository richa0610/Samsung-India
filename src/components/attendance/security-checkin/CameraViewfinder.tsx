import { Ionicons } from "@expo/vector-icons";
import { RefObject } from "react";
import { ActivityIndicator, Image, ImageSourcePropType, Pressable, StyleSheet, View } from "react-native";
import { Camera, CameraDevice, CameraPhotoOutput, CameraRef } from "react-native-vision-camera";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type CameraViewfinderProps = {
  hasPhoto: boolean;
  photoSource: ImageSourcePropType | null;
  hasPermission: boolean;
  requestPermission: () => void;
  device: CameraDevice | undefined;
  // True once no device has been found for a while - see
  // useSecurityCheckIn.DEVICE_TIMEOUT_MS. Shows a real error instead of an
  // indefinite spinner.
  deviceTimedOut: boolean;
  retryDevice: () => void;
  photoOutput: CameraPhotoOutput;
  cameraRef: RefObject<CameraRef | null>;
};

export default function CameraViewfinder({
  hasPhoto,
  photoSource,
  hasPermission,
  requestPermission,
  device,
  deviceTimedOut,
  retryDevice,
  photoOutput,
  cameraRef,
}: CameraViewfinderProps) {
  return (
    <View style={styles.viewfinderBox}>
      {hasPhoto ? (
        <Image source={photoSource ?? undefined} style={styles.photoImage} resizeMode="cover" />
      ) : !hasPermission ? (
        <View style={styles.placeholderBox}>
          <View style={styles.cameraOutlineBox}>
            <Ionicons name="camera-outline" size={72} color="rgba(255, 255, 255, 0.9)" />
          </View>
          <Pressable style={styles.enablePermButton} onPress={requestPermission}>
            <AppText color={Colors.white} weight={FontWeight.medium} style={styles.enablePermText}>
              Enable Camera
            </AppText>
          </Pressable>
        </View>
      ) : !device && deviceTimedOut ? (
        <View style={styles.placeholderBox}>
          <View style={styles.cameraOutlineBox}>
            <Ionicons name="alert-circle-outline" size={64} color="rgba(255, 255, 255, 0.9)" />
          </View>
          <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.errorTitle}>
            Camera failed to start
          </AppText>
          <AppText color="rgba(255, 255, 255, 0.85)" style={styles.errorSubtitle}>
            Check that no other app is using the camera, then try again.
          </AppText>
          <Pressable style={styles.enablePermButton} onPress={retryDevice}>
            <AppText color={Colors.white} weight={FontWeight.medium} style={styles.enablePermText}>
              Retry
            </AppText>
          </Pressable>
        </View>
      ) : !device ? (
        <ActivityIndicator color={Colors.white} />
      ) : (
        <Camera ref={cameraRef} style={styles.cameraStream} device={device} isActive outputs={[photoOutput]} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  viewfinderBox: {
    width: "100%",
    flex: 1,
    minHeight: 340,
    alignSelf: "center",
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#BDBDBD",
    alignItems: "center",
    justifyContent: "center",
    marginVertical: 10,
  },
  placeholderBox: {
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  cameraOutlineBox: {
    width: 140,
    height: 100,
    borderRadius: 18,
    borderWidth: 3,
    borderColor: "rgba(255, 255, 255, 0.8)",
    alignItems: "center",
    justifyContent: "center",
  },
  errorTitle: {
    fontSize: 15,
    textAlign: "center",
  },
  errorSubtitle: {
    fontSize: 12,
    textAlign: "center",
    paddingHorizontal: 24,
    lineHeight: 17,
  },
  enablePermButton: {
    backgroundColor: "rgba(0, 102, 255, 0.85)",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    marginTop: 4,
  },
  enablePermText: {
    fontSize: 11,
  },
  cameraStream: {
    width: "100%",
    height: "100%",
  },
  photoImage: {
    width: "100%",
    height: "100%",
  },
});
