import { StyleSheet, View } from "react-native";

import SmileIcon from "@/assets/images/svg/smile.svg";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";

type ThankYouBannerProps = {
  thankYouText: string;
};

export default function ThankYouBanner({ thankYouText }: ThankYouBannerProps) {
  return (
    <View style={styles.thankYouBox}>
      <View style={styles.thankYouIcon}>
        <SmileIcon width={20} height={20} />
      </View>
      <View style={styles.thankYouTextWrap}>
        <AppText variant="label" style={styles.thankYouText}>
          Thank you!
        </AppText>
        <AppText variant="tiny" color={Colors.gray700} style={styles.thankYouSubtext}>
          {thankYouText}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  thankYouBox: {
    width: "100%",
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#EBFBF3",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#D1FADF",
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  thankYouIcon: {
    width: 30,
    height: 30,
    borderRadius: "50%",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.successTeal,
  },
  thankYouTextWrap: {
    flex: 1,
    gap: 2,
  },
  thankYouText: {
    fontSize: 13.5,
    color: Colors.successTeal,
  },
  thankYouSubtext: {
    fontSize: 11,
    lineHeight: 14,
  },
});
