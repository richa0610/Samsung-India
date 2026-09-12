import { VerifyLocationResult } from "@/api/attendance";
import LocationVerifiedView from "@/components/attendance/LocationVerifiedView";
import { formatDisplayDate } from "@/utils/formatDisplayDate";

type LocationVerifiedStepParams = {
  title?: string;
  time?: string;
  endTime?: string;
  date?: string;
  location?: string;
};

type LocationVerifiedStepProps = {
  params: LocationVerifiedStepParams;
  locationResult: VerifyLocationResult | null;
  verifiedAt: Date | null;
  liveLocationLabel?: string | null;
  onContinue: () => void;
};

export default function LocationVerifiedStep({
  params,
  locationResult,
  verifiedAt,
  liveLocationLabel,
  onContinue,
}: LocationVerifiedStepProps) {
  const formattedTime =
    verifiedAt?.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) || "--";

  return (
    <LocationVerifiedView
      info={{
        sessionTitle: params.title || "Training Session",
        sessionTime: [params.time, params.endTime].filter(Boolean).join(" - ") || params.time || "--",
        date: formatDisplayDate(params.date ?? null),
        location: params.location || "--",
        verifiedTime: formattedTime,
        venueLabel: locationResult?.venueLabel || params.location || undefined,
        liveLocation: liveLocationLabel || undefined,
      }}
      onContinue={onContinue}
    />
  );
}
