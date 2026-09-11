import { StatusBar } from "expo-status-bar";
import { ImageSourcePropType, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Breakpoints } from "@/theme/breakpoints";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import {
  CameraViewfinder,
  NoPhotoControls,
  PhotoCapturedControls,
  SecurityCheckInFooter,
  useSecurityCheckIn,
} from "./security-checkin";

export type SecurityCheckInViewProps = {
  onProceed: (photoSource: ImageSourcePropType) => void;
  onBack?: () => void;
};

export default function SecurityCheckInView({ onProceed }: SecurityCheckInViewProps) {
  const insets = useSafeAreaInsets();
  const {
    hasPermission,
    requestPermission,
    device,
    photoOutput,
    faceDetectorOutput,
    canCapture,
    cameraRef,
    capturing,
    photoSource,
    hasPhoto,
    handleCapture,
    handleRetake,
  } = useSecurityCheckIn();

  const handleProceedPress = () => {
    if (!photoSource) return;
    onProceed(photoSource);
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="dark" animated />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.card}>
          <AppText style={styles.title} weight={FontWeight.semiBold}>
            Security Check-In
          </AppText>
          <AppText style={styles.subtitle}>Please capture a clear photo of your face{"\n"}to verify your identity.</AppText>

          <CameraViewfinder
            hasPhoto={hasPhoto}
            photoSource={photoSource}
            hasPermission={hasPermission}
            requestPermission={requestPermission}
            device={device}
            photoOutput={photoOutput}
            faceDetectorOutput={faceDetectorOutput}
            canCapture={canCapture}
            cameraRef={cameraRef}
          />

          {!hasPhoto ? (
            <NoPhotoControls capturing={capturing} canCapture={canCapture} onCapture={handleCapture} />
          ) : (
            <PhotoCapturedControls onRetake={handleRetake} onProceed={handleProceedPress} />
          )}
        </View>

        <SecurityCheckInFooter hasPhoto={hasPhoto} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    paddingTop: 50,
  },
  statusBarBackground: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 20,
    justifyContent: "space-between",
  },
  card: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    backgroundColor: Colors.white,
    borderRadius: 24,
    padding: 20,
    flex: 1,
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.08, elevation: 3 }),
  },
  title: {
    fontSize: 24,
    color: "#111827",
    textAlign: "center",
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 10,
    lineHeight: 18,
  },
});
