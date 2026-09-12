import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { AssessmentSuiteOut } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type SuiteRowProps = {
  suite: AssessmentSuiteOut;
  onPress: () => void;
};

export default function SuiteRow({ suite, onPress }: SuiteRowProps) {
  return (
    <Pressable style={styles.suiteRow} onPress={onPress}>
      <View style={styles.suiteIcon}>
        <Ionicons name="document-text" size={16} color={Colors.mainColour1} />
      </View>
      <View style={styles.suiteInfo}>
        <AppText style={styles.suiteName} weight={FontWeight.medium}>
          {suite.name}
        </AppText>
        <AppText style={styles.suiteMeta} color={Colors.gray600}>
          {suite.category} • {suite.noOfQuestion} questions
        </AppText>
      </View>
      <Ionicons name="chevron-forward" size={18} color={Colors.gray400} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  suiteRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.gray100,
  },
  suiteIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: Colors.notificationBg,
    alignItems: "center",
    justifyContent: "center",
  },
  suiteInfo: { flex: 1 },
  suiteName: { fontSize: Fonts.bodySm },
  suiteMeta: { fontSize: Fonts.overline, marginTop: 2 },
});
