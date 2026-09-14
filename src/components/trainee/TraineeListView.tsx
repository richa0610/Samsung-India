import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import { DataTable } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { TraineeListItem } from "@/api/trainee";
import { useTraineeListColumns } from "./trainee-list";

type TraineeListViewProps = {
  title: string;
  subtitle: string;
  items: TraineeListItem[];
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  onBack: () => void;
  onEdit: (row: TraineeListItem) => void;
  exportFileName: string;
  emptyLabel: string;
};

export function TraineeListView({
  title,
  subtitle,
  items,
  loading,
  refreshing,
  onRefresh,
  onBack,
  onEdit,
  exportFileName,
  emptyLabel,
}: TraineeListViewProps) {
  const insets = useSafeAreaInsets();
  const columns = useTraineeListColumns(onEdit);

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} style={[styles.banner, { paddingTop: insets.top + 12 }]}>
        <View style={styles.bannerRow}>
          <Pressable onPress={onBack} hitSlop={8}>
            <Ionicons name="arrow-back" size={18} color={Colors.white} />
          </Pressable>
          <View>
            <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold}>{title}</AppText>
            <AppText style={styles.bannerSubtitle} color={Colors.white}>{subtitle}</AppText>
          </View>
        </View>
      </ScreenBanner>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />}
      >
        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator color={Colors.mainColour1} />
          </View>
        ) : (
          <>
            <DataTable
              title={title}
              columns={columns}
              data={items}
              keyExtractor={(row) => row.traineeUid}
              exportFileName={exportFileName}
              searchPlaceholder="Search..."
              emptyLabel={emptyLabel}
            />
            <View style={styles.secureFooter}>
              <Ionicons name="lock-closed" size={12} color={Colors.gray400} />
              <AppText style={styles.secureFooterText} color={Colors.gray400}>Your information is secure</AppText>
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },

  banner: { paddingBottom: 70 },
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  bannerTitle: { fontSize: Fonts.h3 },
  bannerSubtitle: { fontSize: Fonts.overline, marginTop: 2, opacity: 0.9 },

  scroll: { marginTop: -50, zIndex: 1, elevation: 1 },
  content: { paddingHorizontal: 8, paddingVertical: 16, flexGrow: 1 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", paddingVertical: 60 },

  secureFooter: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, paddingVertical: 10 },
  secureFooterText: { fontSize: Fonts.overline },
});
