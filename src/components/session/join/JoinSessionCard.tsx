import CheckCircle from "@/assets/images/svg/check_circle.svg";
import { Pressable, StyleSheet, View } from "react-native";

import AppButton from "@/components/ui/AppButton";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";
import SessionNoticeRow from "./SessionNoticeRow";

type JoinSessionCardProps = {
  details: [string, string][];
  loading: boolean;
  notice: string;
  onJoin: () => void;
  onLogout: () => void;
};

export default function JoinSessionCard({ details, loading, notice, onJoin, onLogout }: JoinSessionCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.details}>
        {details.map(([label, value]) => (
          <View key={label} style={styles.detail}>
            <AppText style={styles.label}>{label}</AppText>
            <AppText style={styles.value} weight={FontWeight.bold}>
              {value}
            </AppText>
          </View>
        ))}
      </View>

      <SessionNoticeRow loading={loading} notice={notice} />

      <AppButton
        title="Join Session"
        onPress={onJoin}
        leftIcon={<CheckCircle width={24} height={24} />}
        buttonStyle={styles.joinButton}
        textStyle={styles.joinButtonText}
      />

      <Pressable onPress={onLogout} hitSlop={8}>
        <AppText style={styles.logout}>Not you ? Logout</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "100%",
    maxWidth: 440,
    backgroundColor: Colors.white,
    borderRadius: 27,
    padding: 24,
    marginTop: "-10%",
    ...createShadow({ x: 0, y: 3, blur: 8, opacity: 0.08, elevation: 5 }),
  },
  details: { flexDirection: "row", flexWrap: "wrap", rowGap: 20 },
  detail: { width: "50%" },
  label: { fontSize: 13, color: "#505050", marginBottom: 6 },
  value: { fontSize: 15, color: "#303030", fontWeight: "bold" },
  joinButton: {
    backgroundColor: "#006AFF",
    height: 48,
    borderRadius: 8,
  },
  joinButtonText: {
    fontSize: 20,
  },
  logout: {
    marginTop: 14,
    textAlign: "center",
    textDecorationLine: "underline",
    fontSize: 13,
    color: "#4D4D4D",
  },
});
