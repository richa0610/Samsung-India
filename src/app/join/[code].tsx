import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { Ionicons } from "@expo/vector-icons";

import AppButton from "@/components/ui/AppButton";
import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import SecurityFooter from "@/components/common/SecurityFooter";
import { useJoinSession } from "@/hooks/useJoinSession";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";

export default function JoinSessionScreen() {
  const { info, error, joining, isLoggedIn, handleJoin, onBack } = useJoinSession();

  const rows: [string, string | null | undefined][] = [
    ["Trainer", info?.trainerName],
    ["Date", info?.date],
    ["Type", info?.sessionType],
    ["Venue", info?.location],
  ];

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <AppCard style={styles.card}>
            <Pressable style={styles.back} onPress={onBack} hitSlop={8}>
              <Ionicons name="arrow-back" size={20} color={Colors.mainColour1} />
            </Pressable>

            <View style={styles.header}>
              <Ionicons name="qr-code" size={28} color={Colors.mainColour1} />
              <AppText variant="h3" style={styles.title}>{"You're joining"}</AppText>
            </View>

            {!info && !error && <ActivityIndicator color={Colors.mainColour1} style={styles.loader} />}
            {error && <AppText style={styles.error}>{error}</AppText>}

            {info && (
              <>
                <AppText variant="h3" style={styles.session}>{info.title}</AppText>
                <AppText style={styles.status}>
                  {info.started ? "Live now" : info.startsAt ? `Starts ${info.startsAt}` : "Not started yet"}
                </AppText>

                <View style={styles.rows}>
                  {rows.filter(([, v]) => v).map(([label, value]) => (
                    <View key={label} style={styles.row}>
                      <AppText style={styles.rowLabel}>{label}</AppText>
                      <AppText style={styles.rowValue}>{value}</AppText>
                    </View>
                  ))}
                </View>

                <AppButton
                  title={isLoggedIn ? "Join Session" : "Continue to Login"}
                  onPress={handleJoin}
                  loading={joining}
                  buttonStyle={styles.button}
                />
                {!isLoggedIn && (
                  <AppText style={styles.hint}>{"New here? You'll register on the next step."}</AppText>
                )}
              </>
            )}
          </AppCard>

          <View style={styles.footer}>
            <SecurityFooter />
          </View>
        </View>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#EEF4FF" },
  content: { flex: 1, justifyContent: "center", alignItems: "center", padding: 20 },
  card: { width: "95%", padding: 22 },
  back: { alignSelf: "flex-start", marginBottom: 6 },
  header: { alignItems: "center", gap: 6, marginBottom: 14 },
  title: { color: Colors.gray600, fontSize: Fonts.body },
  loader: { marginVertical: 20 },
  error: { color: Colors.danger, textAlign: "center", marginVertical: 12, fontSize: Fonts.bodySm },
  session: { textAlign: "center", color: Colors.black },
  status: { textAlign: "center", color: Colors.mainColour1, marginTop: 4, marginBottom: 16, fontSize: Fonts.bodySm },
  rows: { gap: 10, marginBottom: 20 },
  row: { flexDirection: "row", justifyContent: "space-between", gap: 12 },
  rowLabel: { color: Colors.gray600, fontSize: Fonts.bodySm },
  rowValue: { color: Colors.black, fontSize: Fonts.bodySm, flexShrink: 1, textAlign: "right" },
  button: { width: "100%" },
  hint: { textAlign: "center", color: Colors.gray600, fontSize: Fonts.caption, marginTop: 10 },
  footer: { marginTop: 32 },
});
