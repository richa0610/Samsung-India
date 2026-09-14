import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type SurveyHeaderProps = {
  title?: string;
  subtitle?: string;
  instruction?: string;
};

export default function SurveyHeader({
  title = "SECs Feedback | June",
  subtitle = "Classroom Training Sessions",
  instruction = "Please review and complete the form below",
}: SurveyHeaderProps) {
  return (
    <View style={styles.headerCard}>
      <AppText
        style={styles.title}
        color={Colors.black}
        weight={FontWeight.bold}
      >
        {title}
      </AppText>
      {subtitle ? (
        <AppText
          style={styles.subtitle}
          color={Colors.black}
          weight={FontWeight.semiBold}
        >
          {subtitle}
        </AppText>
      ) : null}
      <AppText style={styles.instruction} color={Colors.gray600}>
        {instruction}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  headerCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#E5E7EB",
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
    ...createShadow({ x: 0, y: 2, blur: 6, opacity: 0.04, elevation: 2 }),
  },
  title: {
    fontSize: 16,
    textAlign: "center",
    lineHeight: 22,
  },
  subtitle: {
    fontSize: 15,
    textAlign: "center",
    lineHeight: 21,
    marginTop: 2,
  },
  instruction: {
    fontSize: 12,
    textAlign: "center",
    marginTop: 6,
    lineHeight: 16,
  },
});
