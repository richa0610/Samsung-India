import { useLocalSearchParams } from "expo-router";

import { SecurityCheckInView } from "@/components/attendance";
import {
  AccessGrantedStep,
  CheckInErrorView,
  CheckInLoadingView,
  LocationVerifiedStep,
  useSecureCheckIn,
} from "@/components/attendance/secure-checkin";

export default function SecureCheckInScreen() {
  const params = useLocalSearchParams<{
    conferenceUid: string;
    title?: string;
    location?: string;
    time?: string;
    endTime?: string;
    date?: string;
    mode?: "entry" | "attendance";
  }>();

  const {
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
  } = useSecureCheckIn(params);

  if (step === "locating" || step === "submitting" || locationLoading) {
    return <CheckInLoadingView step={step === "submitting" ? "submitting" : "locating"} />;
  }

  if (step === "error") {
    const isBlocked = permissionState === "blocked" || permissionState === "unavailable";
    const errorMessage = error || locationError || "Couldn't verify your location.";

    return (
      <CheckInErrorView
        errorMessage={errorMessage}
        isBlocked={isBlocked}
        onOpenSettings={openSettings}
        onRetry={startLocationVerification}
        onBack={() => router.back()}
      />
    );
  }

  if (step === "location-verified") {
    return (
      <LocationVerifiedStep
        params={params}
        locationResult={locationResult}
        verifiedAt={verifiedAt}
        liveLocationLabel={liveLocationLabel}
        onContinue={() => setStep("security-checkin")}
      />
    );
  }

  if (step === "security-checkin") {
    return <SecurityCheckInView onProceed={handleProceedFromCheckIn} onBack={() => setStep("location-verified")} />;
  }

  return <AccessGrantedStep params={params} locationResult={locationResult} router={router} />;
}
