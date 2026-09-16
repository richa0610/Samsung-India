import { StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import SecurityFooter from "@/components/common/SecurityFooter";
import { JoinSessionCard, SessionHero, useSessionScreen } from "@/components/session/join";
import { Colors } from "@/theme/colors";

export default function SessionScreen() {
  const { trainee, avatar, loading, notice, details, handleLogout, handleJoinSession } = useSessionScreen();

  return (
    <SafeAreaView style={styles.container}>
      <SessionHero avatar={avatar} name={trainee?.name || "Trainee"} phone={String(trainee?.phone || "")} />

      <View style={styles.content}>
        <JoinSessionCard
          details={details}
          loading={loading}
          notice={notice}
          onJoin={handleJoinSession}
          onLogout={handleLogout}
        />

        <View style={styles.footer}>
          <SecurityFooter />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: {
    flex: 1,
    alignItems: "center",
    paddingHorizontal: 16,
    width: "100%",
  },
  footer: { marginTop: 36 },
});
