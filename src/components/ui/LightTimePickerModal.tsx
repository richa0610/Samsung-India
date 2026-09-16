import { useEffect, useRef, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/theme/colors";

const HOURS = Array.from({ length: 12 }, (_, i) => i + 1);
const MINUTES = Array.from({ length: 60 }, (_, i) => i);

const pad2 = (n: number) => String(n).padStart(2, "0");

function parseInitialTime(val?: string): { hour: number; minute: number; period: "AM" | "PM" } {
  if (val) {
    const match = val.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (match) {
      return {
        hour: Math.max(1, Math.min(12, parseInt(match[1], 10))),
        minute: Math.max(0, Math.min(59, parseInt(match[2], 10))),
        period: match[3].toUpperCase() === "PM" ? "PM" : "AM",
      };
    }
  }
  const now = new Date();
  let h = now.getHours();
  const period: "AM" | "PM" = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return {
    hour: h,
    minute: Math.floor(now.getMinutes() / 5) * 5,
    period,
  };
}

type LightTimePickerModalProps = {
  visible: boolean;
  title?: string;
  value?: string;
  onConfirm: (formattedTime: string) => void;
  onClose: () => void;
};

export default function LightTimePickerModal({
  visible,
  title = "Select Time",
  value,
  onConfirm,
  onClose,
}: LightTimePickerModalProps) {
  const initial = parseInitialTime(value);
  const [hour, setHour] = useState(initial.hour);
  const [minute, setMinute] = useState(initial.minute);
  const [period, setPeriod] = useState<"AM" | "PM">(initial.period);

  const hourScrollRef = useRef<ScrollView>(null);
  const minuteScrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (visible) {
      const parsed = parseInitialTime(value);
      setHour(parsed.hour);
      setMinute(parsed.minute);
      setPeriod(parsed.period);

      setTimeout(() => {
        hourScrollRef.current?.scrollTo({ y: Math.max(0, (parsed.hour - 1) * 36 - 36), animated: true });
        minuteScrollRef.current?.scrollTo({ y: Math.max(0, parsed.minute * 36 - 36), animated: true });
      }, 50);
    }
  }, [visible, value]);

  const handleConfirm = () => {
    onConfirm(`${pad2(hour)}:${pad2(minute)} ${period}`);
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.card} onPress={(e) => e.stopPropagation()}>
          {/* Header */}
          <View style={styles.headerRow}>
            <View style={styles.headerTitleRow}>
              <Ionicons name="time" size={18} color="#0066FF" />
              <AppText style={styles.title}>{title}</AppText>
            </View>
            <Pressable onPress={onClose} hitSlop={8}>
              <Ionicons name="close" size={20} color="#6B7280" />
            </Pressable>
          </View>

          {/* Time Display Banner */}
          <View style={styles.displayBanner}>
            <AppText style={styles.displayText}>
              {pad2(hour)} : {pad2(minute)}
            </AppText>
            <View style={styles.periodBadge}>
              <AppText style={styles.periodBadgeText}>{period}</AppText>
            </View>
          </View>

          {/* AM / PM Toggle */}
          <View style={styles.periodRow}>
            <Pressable
              style={[styles.periodBtn, period === "AM" && styles.periodBtnActive]}
              onPress={() => setPeriod("AM")}
            >
              <AppText style={[styles.periodBtnText, period === "AM" && styles.periodBtnTextActive]}>
                AM
              </AppText>
            </Pressable>
            <Pressable
              style={[styles.periodBtn, period === "PM" && styles.periodBtnActive]}
              onPress={() => setPeriod("PM")}
            >
              <AppText style={[styles.periodBtnText, period === "PM" && styles.periodBtnTextActive]}>
                PM
              </AppText>
            </Pressable>
          </View>

          {/* Selectors: Hours & Minutes */}
          <View style={styles.columnsWrap}>
            <View style={styles.column}>
              <AppText style={styles.columnHeader}>HOUR</AppText>
              <ScrollView
                ref={hourScrollRef}
                style={styles.scrollList}
                showsVerticalScrollIndicator={false}
              >
                {HOURS.map((h) => {
                  const isSelected = h === hour;
                  return (
                    <Pressable
                      key={h}
                      style={[styles.itemPill, isSelected && styles.itemPillActive]}
                      onPress={() => setHour(h)}
                    >
                      <AppText style={[styles.itemText, isSelected && styles.itemTextActive]}>
                        {pad2(h)}
                      </AppText>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>

            <View style={styles.columnDivider} />

            <View style={styles.column}>
              <AppText style={styles.columnHeader}>MINUTE</AppText>
              <ScrollView
                ref={minuteScrollRef}
                style={styles.scrollList}
                showsVerticalScrollIndicator={false}
              >
                {MINUTES.map((m) => {
                  const isSelected = m === minute;
                  return (
                    <Pressable
                      key={m}
                      style={[styles.itemPill, isSelected && styles.itemPillActive]}
                      onPress={() => setMinute(m)}
                    >
                      <AppText style={[styles.itemText, isSelected && styles.itemTextActive]}>
                        {pad2(m)}
                      </AppText>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsRow}>
            <Pressable style={styles.cancelBtn} onPress={onClose}>
              <AppText style={styles.cancelBtnText}>Cancel</AppText>
            </Pressable>
            <Pressable style={styles.confirmBtn} onPress={handleConfirm}>
              <AppText style={styles.confirmBtnText}>Confirm Time</AppText>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(17, 24, 39, 0.45)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 18,
    width: "100%",
    maxWidth: 340,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 8,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  headerTitleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  title: { fontSize: 14, fontWeight: "700", color: "#111827" },
  displayBanner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    backgroundColor: "#EFF6FF",
    borderWidth: 1.2,
    borderColor: "#BFDBFE",
    borderRadius: 14,
    paddingVertical: 10,
    marginBottom: 12,
  },
  displayText: { fontSize: 26, fontWeight: "800", color: "#0066FF", letterSpacing: 1 },
  periodBadge: {
    backgroundColor: "#0066FF",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  periodBadgeText: { fontSize: 11, fontWeight: "800", color: "#FFFFFF" },
  periodRow: { flexDirection: "row", gap: 8, marginBottom: 12 },
  periodBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  periodBtnActive: { backgroundColor: "#0066FF", borderColor: "#0066FF" },
  periodBtnText: { fontSize: 12, fontWeight: "600", color: "#4B5563" },
  periodBtnTextActive: { color: "#FFFFFF", fontWeight: "800" },
  columnsWrap: {
    flexDirection: "row",
    height: 160,
    backgroundColor: "#F9FAFB",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    padding: 8,
    marginBottom: 16,
  },
  column: { flex: 1, alignItems: "center" },
  columnHeader: {
    fontSize: 9.5,
    fontWeight: "700",
    color: "#6B7280",
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  columnDivider: { width: 1, backgroundColor: "#E5E7EB", marginVertical: 4 },
  scrollList: { width: "100%", paddingHorizontal: 6 },
  itemPill: {
    paddingVertical: 6,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    marginVertical: 2,
  },
  itemPillActive: { backgroundColor: "#0066FF" },
  itemText: { fontSize: 13, fontWeight: "600", color: "#374151" },
  itemTextActive: { color: "#FFFFFF", fontWeight: "800" },
  actionsRow: { flexDirection: "row", gap: 10 },
  cancelBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
  },
  cancelBtnText: { fontSize: 12, fontWeight: "700", color: "#4B5563" },
  confirmBtn: {
    flex: 1.4,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0066FF",
    borderRadius: 10,
  },
  confirmBtnText: { fontSize: 12, fontWeight: "800", color: "#FFFFFF" },
});
