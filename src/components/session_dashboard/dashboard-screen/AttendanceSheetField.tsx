import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type AttendanceSheetFieldProps = {
  fileName: string | null;
  onPick: () => void;
  onClear: () => void;
};

export default function AttendanceSheetField({ fileName, onPick, onClear }: AttendanceSheetFieldProps) {
  if (!fileName) {
    return (
      <Pressable style={styles.uploadBtn} onPress={onPick} accessibilityRole="button">
        <Ionicons name="cloud-upload-outline" size={18} color="#0066FF" />
        <AppText color="#0066FF" weight={FontWeight.semiBold} style={styles.uploadText}>
          Upload Attendance Sheet
        </AppText>
      </Pressable>
    );
  }

  return (
    <View style={styles.fileRow}>
      <Ionicons name="document-text-outline" size={16} color="#374151" />
      <AppText style={styles.fileName} numberOfLines={1}>
        {fileName}
      </AppText>
      <Pressable onPress={onClear} hitSlop={8} accessibilityLabel="Remove attendance sheet">
        <Ionicons name="close-circle" size={18} color="#9CA3AF" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  uploadBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#BFDBFE",
    backgroundColor: "#EFF6FF",
    marginTop: 12,
  },
  uploadText: { fontSize: 14 },
  fileRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    height: 44,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: Colors.white,
    marginTop: 12,
  },
  fileName: { flex: 1, fontSize: 12, color: "#374151" },
});
