import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { ApiError, SessionHistoryItem, getSessionHistory } from "@/api/session";

type Props = {
  visible: boolean;
  onClose: () => void;
  token: string | null;
};

export default function RecentSessionsModal({ visible, onClose, token }: Props) {
  const [items, setItems] = useState<SessionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!token || !visible) return;
      setLoading(true);
      setError(null);
      try {
        const history = await getSessionHistory(token);
        if (!ignore) {
          setItems(history);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof ApiError ? err.message : "Couldn't load your recent sessions.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, [token, visible]);

  return (
    <AppModal
      visible={visible}
      onClose={onClose}
      position="center"
      title="Recent Sessions"
      subtitle="Your past sessions and results"
      showCloseButton
      contentStyle={styles.sheet}
    >
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator color={Colors.mainColour1} />
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <AppText style={styles.emptyText} color={Colors.gray600}>{error}</AppText>
        </View>
      ) : items.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="time-outline" size={32} color={Colors.gray400} />
          <AppText style={styles.emptyText} color={Colors.gray600}>No past sessions yet.</AppText>
        </View>
      ) : (
        <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
          {items.map((item) => (
            <View key={item.conferenceUid} style={styles.row}>
              <View style={styles.rowInfo}>
                <AppText style={styles.rowTitle} weight={FontWeight.medium}>{item.title}</AppText>
                <AppText style={styles.rowMeta} color={Colors.gray600}>
                  {item.date ?? "--"}{item.trainerName ? ` • ${item.trainerName}` : ""}
                </AppText>
              </View>
              <View style={styles.rowBadges}>
                {item.attendanceStatus && (
                  <View style={[styles.badge, { backgroundColor: "#DCFCE7" }]}>
                    <AppText style={[styles.badgeText, { color: Colors.success }]}>{item.attendanceStatus}</AppText>
                  </View>
                )}
                {item.score && (
                  <View style={[styles.badge, { backgroundColor: item.passed ? "#DCFCE7" : "#FEE2E2" }]}>
                    <AppText style={[styles.badgeText, { color: item.passed ? Colors.success : Colors.danger }]}>
                      {item.score}
                    </AppText>
                  </View>
                )}
              </View>
            </View>
          ))}
        </ScrollView>
      )}
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { paddingHorizontal: 16, paddingBottom: 20, maxHeight: "75%", width: "90%" },
  centered: { alignItems: "center", justifyContent: "center", gap: 8, paddingVertical: 32 },
  emptyText: { fontSize: Fonts.bodySm, textAlign: "center" },
  list: { maxHeight: 380 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray100,
  },
  rowInfo: { flex: 1 },
  rowTitle: { fontSize: Fonts.bodySm },
  rowMeta: { fontSize: Fonts.overline, marginTop: 2 },
  rowBadges: { flexDirection: "row", gap: 6 },
  badge: { borderRadius: Radius.pill, paddingHorizontal: 9, paddingVertical: 3 },
  badgeText: { fontSize: Fonts.overline, fontWeight: "600" },
});
