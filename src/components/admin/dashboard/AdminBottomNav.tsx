import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import AdminMenuSheet, { AdminMenuSheetItem } from "./AdminMenuSheet";

export type AdminDashboardTab = "home" | "training" | "attendance";

type AdminBottomNavProps = {
  activeTab: AdminDashboardTab;
  /** Shown as a red badge on the Training tab (pending reviews) - omit/0 hides it. */
  pendingCount?: number;
  /** Called for Home - Training and Attendance open their own menu sheets. */
  onSelectTab: (tab: AdminDashboardTab) => void;
};

const TABS: { key: AdminDashboardTab; label: string; icon: keyof typeof Ionicons.glyphMap; activeIcon: keyof typeof Ionicons.glyphMap }[] = [
  { key: "home", label: "Home", icon: "home-outline", activeIcon: "home" },
  { key: "training", label: "Training", icon: "school-outline", activeIcon: "school" },
  { key: "attendance", label: "Attendance", icon: "people-outline", activeIcon: "people" },
];

type SheetTab = "training" | "attendance";

const ATTENDANCE_ITEMS: AdminMenuSheetItem[] = [
  { key: "list", label: "Attendance List", icon: "reader-outline" },
  { key: "confirmed", label: "Confirmed Attendance", icon: "calendar-outline" },
  { key: "pending", label: "Pending Attendance", icon: "hourglass-outline" },
];

export default function AdminBottomNav({ activeTab, pendingCount = 0, onSelectTab }: AdminBottomNavProps) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [openSheet, setOpenSheet] = useState<SheetTab | null>(null);

  const trainingItems: AdminMenuSheetItem[] = [
    { key: "new", label: "New Training", icon: "school-outline" },
    { key: "pending", label: "Pending Training", icon: "document-text-outline", badge: pendingCount },
    { key: "list", label: "Training List", icon: "list-outline" },
  ];

  const handleSheetItem = (key: string) => {
    const sheet = openSheet;
    setOpenSheet(null);
    if (sheet === "training") {
      if (key === "new") router.push("/add_training");
      else if (key === "pending") router.push("/admin_pending_trainings");
      else router.push("/admin_training_list");
    } else if (sheet === "attendance") {
      if (key === "confirmed") router.push("/admin_confirmed_attendance");
      else if (key === "pending") router.push("/admin_pending_attendance");
      else router.push("/admin_attendance_list");
    }
  };

  const handlePressTab = (tab: AdminDashboardTab) => {
    if (tab === "training" || tab === "attendance") {
      setOpenSheet((open) => (open === tab ? null : tab));
    } else {
      setOpenSheet(null);
      onSelectTab(tab);
    }
  };

  const renderTabs = (highlighted: AdminDashboardTab) =>
    TABS.map((tab) => {
      const isActive = highlighted === tab.key;
      const color = isActive ? Colors.mainColour1 : "#6B7280";
      return (
        <Pressable
          key={tab.key}
          style={styles.tabItem}
          onPress={() => handlePressTab(tab.key)}
          accessibilityRole="tab"
          accessibilityState={{ selected: isActive }}
        >
          <View>
            <Ionicons name={isActive ? tab.activeIcon : tab.icon} size={20} color={color} />
            {tab.key === "training" && pendingCount > 0 && (
              <View style={styles.badge}>
                <AppText style={styles.badgeText} color={Colors.white} weight={FontWeight.bold}>
                  {pendingCount > 99 ? "99+" : pendingCount}
                </AppText>
              </View>
            )}
          </View>
          <AppText numberOfLines={1} style={[styles.tabLabel, { color }, isActive && styles.activeTabLabel]}>
            {tab.label}
          </AppText>
        </Pressable>
      );
    });

  const bottomPadding = Math.max(insets.bottom, 8);

  return (
    <>
      <View style={[styles.container, { paddingBottom: bottomPadding }]}>{renderTabs(activeTab)}</View>
      <AdminMenuSheet
        visible={openSheet !== null}
        onClose={() => setOpenSheet(null)}
        items={openSheet === "attendance" ? ATTENDANCE_ITEMS : trainingItems}
        onSelect={handleSheetItem}
        footer={
          <View style={[styles.sheetNav, { paddingBottom: bottomPadding }]}>
            {renderTabs(openSheet ?? activeTab)}
          </View>
        }
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    backgroundColor: Colors.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingVertical: 6,
    borderTopWidth: 1,
    borderColor: "#F3F4F6",
    ...Shadows.raised,
  },
  sheetNav: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    paddingVertical: 6,
    borderTopWidth: 1,
    borderColor: "#F3F4F6",
  },
  tabItem: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 2,
    flex: 1,
  },
  badge: {
    position: "absolute",
    top: -4,
    right: -8,
    backgroundColor: Colors.danger,
    borderRadius: Radius.pill,
    minWidth: 15,
    height: 15,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
  },
  badgeText: { fontSize: 8.5 },
  tabLabel: {
    fontSize: 9.5,
    marginTop: 2,
    fontWeight: "500",
  },
  activeTabLabel: {
    fontWeight: "700",
  },
});
