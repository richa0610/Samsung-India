import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { Colors } from "@/theme/colors";
import { formatMonthDay } from "../calendarUtils";

type RangeInfoBannerProps = {
  selectedStart: Date | null;
  selectedEnd: Date | null;
};

export default function RangeInfoBanner({ selectedStart, selectedEnd }: RangeInfoBannerProps) {
  return (
    <View style={styles.infoBanner}>
      <View style={styles.infoIconCircle}>
        <Ionicons name="information" size={11} color={Colors.white} />
      </View>
      {selectedStart && selectedEnd ? (
        <AppText style={styles.infoText}>
          Showing data from <AppText style={styles.infoHighlight}>{formatMonthDay(selectedStart)}</AppText> to{" "}
          <AppText style={styles.infoHighlight}>{formatMonthDay(selectedEnd)}</AppText>.
        </AppText>
      ) : (
        <AppText style={styles.infoText}>A date left empty defaults to today when you tap Filter.</AppText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  infoBanner: {
    marginTop: 8,
    backgroundColor: Colors.blue50,
    borderRadius: 10,
    paddingVertical: 6,
    paddingHorizontal: 8,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  infoIconCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
  },
  infoText: {
    flex: 1,
    fontSize: 9.5,
    color: Colors.gray800,
    lineHeight: 13,
  },
  infoHighlight: {
    fontSize: 9.5,
    color: Colors.mainColour1,
    fontWeight: "700",
  },
});
