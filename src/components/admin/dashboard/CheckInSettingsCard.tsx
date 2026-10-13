import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Switch, View } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { useCheckInSettings } from "@/hooks/useCheckInSettings";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

const LABEL = "Face detection at check-in";

/** Super Admin only: whether this company's trainees pass a face check before the check-in
 *  photo, or just capture it. Renders nothing for any other account. */
export default function CheckInSettingsCard() {
  const { settings, saving, setFaceDetection } = useCheckInSettings();
  if (!settings) return null;
  const on = settings.faceDetectionEnabled;

  return (
    <View style={styles.section}>
      <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray500} style={styles.sectionLabel}>
        SETTINGS
      </AppText>
      <AppCard style={styles.card}>
        <View style={styles.icon}>
          <Ionicons name="scan-outline" size={20} color={Colors.mainColour1} />
        </View>
        <View style={styles.text}>
          <AppText weight={FontWeight.semiBold} color={Colors.black} style={styles.title}>
            {LABEL}
          </AppText>
          <AppText color={Colors.gray500} style={styles.subtitle}>
            {on ? "Trainees pass a face check before the photo." : "Trainees just capture a photo."}
          </AppText>
        </View>
        <Switch
          value={on}
          onValueChange={setFaceDetection}
          disabled={saving}
          trackColor={{ false: Colors.gray300, true: Colors.mainColour1 }}
          thumbColor={on ? Colors.white : Colors.gray400}
          ios_backgroundColor={Colors.gray300}
          accessibilityLabel={LABEL}
        />
      </AppCard>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { paddingHorizontal: 16, paddingTop: 10 },
  sectionLabel: { letterSpacing: 0.8, paddingHorizontal: 4, paddingBottom: 6 },
  card: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  icon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: Colors.brandTintSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  text: { flex: 1, gap: 2 },
  title: { fontSize: Fonts.bodySm },
  subtitle: { fontSize: Fonts.overline },
});
