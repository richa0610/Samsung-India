import { Ionicons } from "@expo/vector-icons";
import { RefObject } from "react";
import { ActivityIndicator, Image, ImageSourcePropType, Pressable, StyleSheet, View } from "react-native";
import { Camera, CameraDevice, CameraOutput, CameraPhotoOutput, CameraRef } from "react-native-vision-camera";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type CameraViewfinderProps = {
  hasPhoto: boolean;
  photoSource: ImageSourcePropType | null;
  hasPermission: boolean;
  requestPermission: () => void;
  device: CameraDevice | undefined;
  photoOutput: CameraPhotoOutput;
  faceDetectorOutput: CameraOutput;
  // False while no face is in view (real device only - see useSecurityCheckIn) -
  // shows a "position your face" hint over the live preview.
  canCapture: boolean;
  cameraRef: RefObject<CameraRef | null>;
};

export default function CameraViewfinder({
  hasPhoto,
  photoSource,
  hasPermission,
  requestPermission,
  device,
  photoOutput,
  faceDetectorOutput,
  canCapture,
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
      ) : !device ? (
        <ActivityIndicator color={Colors.white} />
      ) : (
        <>
          <Camera
            ref={cameraRef}
            style={styles.cameraStream}
            device={device}
            isActive
            outputs={[photoOutput, faceDetectorOutput]}
          />
          {!canCapture && (
            <View style={styles.faceHintBanner} pointerEvents="none">
              <Ionicons name="scan-outline" size={16} color={Colors.white} />
              <AppText color={Colors.white} weight={FontWeight.medium} style={styles.faceHintText}>
                Position your face in the frame
              </AppText>
            </View>
          )}
        </>
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
  faceHintBanner: {
    position: "absolute",
    left: 12,
    right: 12,
    bottom: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: "rgba(17, 24, 39, 0.75)",
  },
  faceHintText: {
    fontSize: 12,
  },
});
