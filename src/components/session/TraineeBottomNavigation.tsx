import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import HomeIcon from "@/assets/images/svg/home.svg";
import AppText from "@/components/ui/AppText";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";

export type TraineeBottomNavigationProps = {
  activeTab: TraineeTab;
  onSelectTab: (tab: TraineeTab) => void;
};

// All four tabs render identically (icon in a circular badge + label below) -
// the only thing that marks one as active is a blue fill behind its own
// icon, not a raised/oversized button. Kept as data so the four Pressables
// below share exactly the same layout instead of one being special-cased.
const TABS: {
  key: TraineeTab;
  label: string;
  icon: (active: boolean) => React.ReactNode;
}[] = [
  {
    key: "rank",
    label: "Rank",
    icon: (active) => (
      <Ionicons name={active ? "podium" : "podium-outline"} size={20} color={active ? Colors.white : Colors.bottomNavInactive} />
    ),
  },
  {
    key: "dashboard",
    label: "Dashboard",
    icon: (active) => (
      <Ionicons name={active ? "grid" : "grid-outline"} size={19} color={active ? Colors.white : Colors.bottomNavInactive} />
    ),
  },
  {
    key: "home",
    label: "Home",
    icon: (active) => <HomeIcon width={20} height={20} stroke={active ? Colors.white : Colors.bottomNavInactive} />,
  },
  {
    key: "profile",
    label: "Profile",
    icon: (active) => (
      <Ionicons
        name={active ? "person-circle" : "person-circle-outline"}
        size={22}
        color={active ? Colors.white : Colors.bottomNavInactive}
      />
    ),
  },
];

export default function TraineeBottomNavigation({
  activeTab = "home",
  onSelectTab,
}: TraineeBottomNavigationProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.wrapper, { paddingBottom: Math.max(insets.bottom, 12) }]}>
      <View style={styles.container}>
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <Pressable
              key={tab.key}
              style={({ pressed }) => [styles.tabItem, pressed && styles.tabItemPressed]}
              onPress={() => onSelectTab(tab.key)}
              accessibilityRole="button"
              accessibilityLabel={tab.label}
              hitSlop={8}
            >
              <View style={[styles.iconBadge, active && styles.iconBadgeActive]}>{tab.icon(active)}</View>
              <AppText
                style={[styles.tabLabel, active && styles.tabLabelActive]}
                weight={active ? FontWeight.bold : FontWeight.medium}
              >
                {tab.label}
              </AppText>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: Colors.white,
    borderTopLeftRadius: Radius.nav,
    borderTopRightRadius: Radius.nav,
    ...Shadows.footer,
  },
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  tabItem: {
    alignItems: "center",
    justifyContent: "center",
    minWidth: 64,
    gap: 4,
  },
  tabItemPressed: {
    opacity: 0.75,
  },
  iconBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  iconBadgeActive: {
    backgroundColor: Colors.headerBlue,
  },
  tabLabel: {
    fontSize: Fonts.caption,
    color: Colors.bottomNavInactive,
  },
  tabLabelActive: {
    color: Colors.headerBlue,
  },
});
