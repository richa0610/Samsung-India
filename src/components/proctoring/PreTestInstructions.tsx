import { ScrollView, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Fonts } from "@/theme/fonts";
import { AgreeAndStart, PoseChecklistCard, RulesCard, WarningNotice } from "./pre-test";

type Props = {
  onStart: () => void;
};

export default function PreTestInstructions({ onStart }: Props) {
  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={styles.content}>
        <AppText style={styles.title} weight={FontWeight.semiBold}>
          Before You Begin
        </AppText>
        <AppText style={styles.subtitle} color={Colors.gray600}>
          Please read the following instructions carefully.
        </AppText>

        <RulesCard />
        <PoseChecklistCard />
        <WarningNotice />
        <AgreeAndStart onStart={onStart} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, gap: 14, paddingBottom: 32 },
  title: { fontSize: Fonts.h2, textAlign: "center" },
  subtitle: { fontSize: Fonts.bodySm, textAlign: "center", marginBottom: 4 },
});
