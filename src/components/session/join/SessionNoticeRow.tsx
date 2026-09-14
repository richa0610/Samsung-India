import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";

type SessionNoticeRowProps = {
  loading: boolean;
  notice: string;
};

export default function SessionNoticeRow({ loading, notice }: SessionNoticeRowProps) {
  return (
    <View style={styles.notice}>
      {loading ? (
        <ActivityIndicator size="small" color={Colors.mainColour1} />
      ) : (
        <Ionicons name="information-circle-outline" size={14} color="#3D3D3D" />
      )}
      <AppText style={styles.noticeText}>{loading ? "Checking for your session…" : notice}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 26,
    marginBottom: 13,
  },
  noticeText: {
    flex: 1,
    fontSize: 11,
    color: "#3D3D3D",
    marginLeft: 4,
  },
});
